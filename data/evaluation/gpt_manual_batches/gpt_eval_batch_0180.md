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
{"candidate_id": "LLM04476", "doc_id": "NCT03083197_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to tetracycline, doxycycline or azithromycin Administration of doxycycline, azithromycin, chloramphenicol, rifampicin, or tetracycline during the preceding 7 days Pregnancy or breast-feeding Patients with myasthenia gravis or systemic lupus erythematosus Patients with an established infection (diagnostic test required) e.g. acute malaria, dengue, leptospirosis, typhoid, Japanese encephalitis etc. Current TB or TB treatment in = 6 months (contain active antibiotics against Orientia spp.) Current HAART use for HIV, long term use of immunosuppressants (e.g. steroids, chemotherapy, TNF-inhibitors and related agents) Patients with severe disease whom the clinical team feel their condition necessitates the need for additional scrub typhus treatment beyond the allocated antibiotic treatment assigned at randomization (e.g. IV chloramphenicol and/or PO/NG rifampicin)", "candidate_expression": "((HIV) AND (diagnostic test) AND (during the preceding 7 days) AND (hypersensitivity) AND (in = 6 months) AND (infection) AND (long term use) AND ((Pregnancy) OR (breast-feeding)) AND ((myasthenia gravis) OR (systemic lupus erythematosus)) AND ((Japanese encephalitis) OR (acute malaria) OR (dengue) OR (leptospirosis) OR (typhoid)) AND ((TB) OR (TB treatment)) AND ((HAART) OR (immunosuppressants)) AND ((TNF-inhibitors) OR (chemotherapy) OR (steroids)) AND ((azithromycin) OR (doxycycline) OR (tetracycline)) AND ((azithromycin) OR (chloramphenicol) OR (doxycycline) OR (rifampicin) OR (tetracycline)))"}
{"candidate_id": "LLM04477", "doc_id": "NCT03278548_inc", "case_bucket": "or", "source_criterion": "Patients undergoing elective abdominal surgery with an expected blood loss of = 500 ml ASA Physical Status II - III Signed written informed consent form Body weight = 140 kg Sepsis Burns Renal impairment (AKIN stage = 1) or acute and/or chronic renal replacement therapy Intracranial or cerebral haemorrhage Critically ill patients (typically admitted to the intensive care unit) Hyperhydration Pulmonary oedema Dehydration Hyperkalaemia Severe hypernatraemia Severe hyperchloraemia Severely impaired hepatic function Congestive heart failure Severe coagulopathy Organ transplant patients Metabolic alkalosis Simultaneous participation in another interventional clinical trial (drugs or medical devices studies)", "candidate_expression": "((= 1) AND (= 140 kg) AND (= 500 ml) AND (AKIN stage) AND (ASA Physical Status) AND (Body weight) AND (Burns) AND (Congestive heart failure) AND (Critically ill) AND (Dehydration) AND (Hyperhydration) AND (Hyperkalaemia) AND (II - III) AND (Metabolic alkalosis) AND (Organ transplant) AND (Pulmonary oedema) AND (Sepsis) AND (Severe) AND (Severely) AND (Signed written informed consent form) AND (Simultaneous participation in another interventional clinical trial (drugs or medical devices studies)) AND (abdominal surgery) AND (admitted) AND (coagulopathy) AND (elective) AND (expected blood loss) AND (hyperchloraemia) AND (hypernatraemia) AND (impaired hepatic function) AND (intensive care unit) AND (typically) AND ((Renal impairment) OR (renal replacement therapy)) AND ((acute) OR (chronic)) AND ((Intracranial haemorrhage) OR (cerebral haemorrhage)))"}
{"candidate_id": "LLM04478", "doc_id": "NCT02083991_inc", "case_bucket": "or", "source_criterion": "First or second single kidney (cadaveric or living donors) transplant recipients. Considered for a standard immunosuppressive protocol. Must be capable of giving written informed connect for participation in the study for 24 months.", "candidate_expression": "((Must be capable of giving written informed connect for participation in the study for 24 months.) AND (standard immunosuppressive protocol Considered for) AND ((First single kidney transplant) OR (transplant second single kidney)) AND ((cadaveric donors) OR (living donors)))"}
{"candidate_id": "LLM04479", "doc_id": "NCT01218737_exc", "case_bucket": "or", "source_criterion": "Surgery and/or previous ocular pathology (presence of scar/change in the cornea, glaucoma, retinopathies, etc.). Patient has diabetes or is immunodepressed. Any systemic infection during the study. Signs and/or symptoms of ocular inflammation/infection (bacterial, viral, fungal, caused by Chlamydia, by Mycobacterium, Acanthamoeba or of allergic etiology). Have used any systemic or topical antibiotics for ocular infection in the previous 14 days. Patient has known hypersensitivity to any of the components of the formulations used in the study.", "candidate_expression": "((Acanthamoeba systemic) AND (Chlamydia) AND (Mycobacterium) AND (hypersensitivity components of the formulations) AND (infection systemic during the study) AND (ocular infection) AND ((Surgery) OR (ocular pathology previous)) AND ((ocular infection) OR (ocular inflammation)) AND ((allergic etiology) OR (bacterial etiology) OR (caused by Acanthamoeba) OR (caused by Chlamydia) OR (caused by Mycobacterium) OR (fungal etiology) OR (viral etiology)) AND ((systemic antibiotics) OR (topical antibiotics topical)) AND ((change in the cornea) OR (glaucoma) OR (retinopathies) OR (scar)) AND ((diabetes) OR (immunodepressed)))"}
{"candidate_id": "LLM04480", "doc_id": "NCT03639545_exc", "case_bucket": "or", "source_criterion": "diagnosed advanced heart, kidney or liver failure benign prostatic hyperplasia prostatic carcinoma frequent urinary tract infections non-type 1 diabetes mellitus", "candidate_expression": "((advanced heart failure) AND (benign prostatic hyperplasia) AND (kidney failure) AND (liver failure) AND (non-type 1 diabetes mellitus) AND (prostatic carcinoma) AND (urinary tract infections frequent))"}
{"candidate_id": "LLM04481", "doc_id": "NCT02785549_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04482", "doc_id": "NCT02874092_exc", "case_bucket": "or", "source_criterion": "History of sensitivity to study medications or any of their excipients RA cohort: Previous intolerance to MTX Current treatment with antiplatelet therapy Absolute indication for anti-platelet therapy Need for chronic oral anticoagulant therapy Severe hepatic impairment (eg, ascites and/or clinical signs of coagulopathy) Renal failure (eGFR <30 or requiring dialysis) A known bleeding diathesis, hemostatic or coagulation disorder, or prior major bleeding Prior stroke Active pathological bleeding History of intracranial haemorrhage Life expectancy <12 months based on investigator's judgement Patients considered to be at risk of bradycardic events (e.g., known sick sinus syndrome or second or third degree atrioventricular [AV)] block) unless already treated with a permanent pacemaker Anemia (hematocrit < 27%) Platelet count < 100,000/ml Concomitant use of strong CYP 3A inhibitors or inducers History of thrombocytopenia or neutropenia Pregnant or nursing women, or females with a positive pregnancy test at screening Females of child bearing potential not using acceptable method of birth control prior to or during study Concern for inability of the patient to comply with study procedures and/or follow up (eg, alcohol or drug abuse)", "candidate_expression": "((< 100,000/ml) AND (< 27%) AND (<12 months) AND (<30) AND (Absolute indication for) AND (Active) AND (Anemia) AND (Concern for) AND (Current) AND (Females) AND (History) AND (Life expectancy) AND (MTX) AND (Need for) AND (Platelet count) AND (Prior) AND (RA) AND (Renal failure) AND (Severe hepatic impairment) AND (acceptable) AND (anti-platelet therapy) AND (antiplatelet therapy) AND (at risk of) AND (at screening) AND (bradycardic events) AND (child bearing potential) AND (chronic oral anticoagulant therapy) AND (clinical signs of) AND (females) AND (hematocrit) AND (intolerance) AND (intracranial haemorrhage) AND (method of birth control) AND (not) AND (pathological bleeding) AND (permanent pacemaker) AND (positive) AND (pregnancy test) AND (prior) AND (requiring) AND (screening) AND (sensitivity) AND (stroke) AND (study medications) AND (unless) AND (women) AND ((ascites) OR (coagulopathy)) AND ((dialysis) OR (eGFR)) AND ((bleeding diathesis) OR (coagulation disorder) OR (hemostatic disorder) OR (major bleeding)) AND ((second degree atrioventricular [AV)] block) OR (sick sinus syndrome) OR (third degree atrioventricular [AV)] block)) AND ((strong CYP 3A inducers) OR (strong CYP 3A inhibitors)) AND ((neutropenia) OR (thrombocytopenia)) AND ((Pregnant) OR (nursing)) AND ((during study) OR (prior to study)) AND ((inability to comply with follow up) OR (inability to comply with study procedures)) AND ((alcohol abuse) OR (drug abuse)))"}
{"candidate_id": "LLM04483", "doc_id": "NCT02432404_exc", "case_bucket": "or", "source_criterion": "Current pregnancy Desire/intent to become pregnant over the course of the study Women who are less than 6 weeks postpartum Contraindications to hormonal contraceptive use per package insert, including history of deep vein thrombosis, smoking in women older than 35 years Current IUD Unable to comprehend consent material because of language barrier or psychological difficulty", "candidate_expression": "((Contraindications to hormonal contraceptive) AND (Desire/intent to become pregnant over the course of the study) AND (IUD) AND (Unable to comprehend consent material because of language barrier or psychological difficulty) AND (Women less than 6 weeks postpartum) AND (deep vein thrombosis) AND (hormonal contraceptive) AND (pregnancy) AND (pregnant) AND (women smoking older than 35 years))"}
{"candidate_id": "LLM04484", "doc_id": "NCT03481894_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to egg, soybean proteins, peanut proteins, corn or corn products, or to any of the active substances or excipients Severe hyperlipidemia or severe disorders of lipid metabolism characterized by hypertriglyceridemia (serum triglyceride concentration >1,000 g/dL). Inborn errors of amino acid metabolism Cardiopulmonary instability (including pulmonary edema, cardiac insufficiency, myocardial infarction, acidosis and hemodynamic instability requiring significant vasopressor support) Hemophagocytic syndrome. PN in the last 7 days prior to study enrollment. Need for chronic PN before study start Liver enzymes (either AST, ALT, GGPT), or direct bilirubin exceeding 2 x upper limit of normal range Pathologically altered level of any serum electrolyte (sodium, potassium, magnesium, calcium, chloride, phosphate) unless corrected prior to the start of study treatment Pathologically altered blood pH, or oxygen saturation, or carbon dioxide unless corrected prior to the start of study treatment Pregnancy or lactation Participation in another clinical study", "candidate_expression": "((Cardiopulmonary instability) AND (Hemophagocytic syndrome) AND (Inborn errors of amino acid metabolism) AND (PN in the last 7 days prior to study enrollment) AND (Participation in another clinical study) AND (chronic PN before study start) AND (hypersensitivity) AND (level of any serum electrolyte Pathologically altered) AND (serum triglyceride concentration >1,000 g/dL) AND (vasopressor) AND ((disorders of lipid metabolism severe) OR (hyperlipidemia Severe) OR (hypertriglyceridemia)) AND ((acidosis) OR (cardiac insufficiency) OR (hemodynamic instability vasopressor support) OR (myocardial infarction) OR (pulmonary edema)) AND ((Liver enzymes) OR (direct bilirubin)) AND ((ALT) OR (AST) OR (GGPT)) AND ((calcium) OR (chloride) OR (magnesium) OR (phosphate) OR (potassium) OR (sodium)) AND ((blood pH) OR (carbon dioxide) OR (oxygen saturation)) AND ((Pregnancy) OR (lactation)) AND ((active substances) OR (corn) OR (corn products) OR (egg) OR (excipients) OR (peanut proteins) OR (soybean proteins)))"}
{"candidate_id": "LLM04485", "doc_id": "NCT02371200_exc", "case_bucket": "other", "source_criterion": "1. Does not have a documented history of generalized seizures. 2. Has not had a GTC seizure within the last year AND is not expected to have a reduction of anti-epileptic drugs during their hospital admission. 3. Intracranial EEG electrodes are being used 4. The subject's upper arm circumference not adequate for proper fit of the EMG monitor (less than 14cm). 5. Pregnant female. 6. Subject/Caregiver is unable to provide consent.", "candidate_expression": "((Intracranial EEG electrodes) AND (Pregnant less than 14cm) AND (Subject/Caregiver is unable to provide consent.) AND (anti-epileptic drugs) AND (female) AND (upper arm circumference adequate for proper fit of the EMG monitor) AND NOT (GTC seizure within the last year) AND NOT (reduction of anti-epileptic drugs during their hospital admission) AND NOT (generalized seizures history))"}
{"candidate_id": "LLM04486", "doc_id": "NCT03366779_inc", "case_bucket": "or", "source_criterion": "Age 18 to 75 years old (male or female). Patients with posterior or posterolateral disc herniations at one level between L1 and S1 with radiographic confirmation of neural compression using CT and/or MRI. At least six (6) weeks of failed, conservative treatment prior to surgery, or requires immediate surgery to prevent permanent disability. Minimum posterior disc height of 5mm at the index level(s). Lower back pain and/or sciatica with or without spinal claudication. Oswestry Questionnaire score of at least 40/100 at baseline. VAS leg pain of at least 40/100 at baseline. Psychosocially, mentally and physically able to fully comply with the clinical protocol and willing to adhere to follow-up schedule and requirements.", "candidate_expression": "((Age 18 to 75 years old) AND (CT) AND (Lower back pain) AND (MRI) AND (Oswestry Questionnaire score at least 40/100 at baseline) AND (Psychosocially, mentally and physically able to fully comply with the clinical protocol and willing to adhere to follow-up schedule and requirements.) AND (VAS leg pain at least 40/100 at baseline) AND (disc herniations one level between L1 and S1 radiographic confirmation) AND (female posterior posterolateral) AND (male) AND (neural compression) AND (permanent disability prevent) AND (posterior disc height Minimum of 5mm index level(s)) AND (radiographic) AND (sciatica) AND (spinal claudication) AND (surgery immediate) AND (treatment At least six (6) weeks failed conservative prior to surgery))"}
{"candidate_id": "LLM04487", "doc_id": "NCT02380118_exc", "case_bucket": "or", "source_criterion": "known hypersensitivity or contraindication to the study drugs reversible aetiology for agitation (e.g. hypotension, hypoxia, hypoglycaemia) known pregnancy acute alcohol withdrawal patients aged>75 years.", "candidate_expression": "((acute alcohol withdrawal) AND (aged >75 years) AND (agitation) AND (contraindication) AND (hypersensitivity) AND (hypoglycaemia) AND (hypotension) AND (hypoxia) AND (pregnancy) AND (reversible aetiology) AND (study drugs))"}
{"candidate_id": "LLM04488", "doc_id": "NCT02528136_inc", "case_bucket": "other", "source_criterion": "Healthy pregnant women age 18 to 50 Singleton pregnancy at gestational age 36 weeks or more Able to read and understand Norwegian.", "candidate_expression": "((Able to read and understand Norwegian) AND (Healthy) AND (Singleton pregnancy) AND (age 18 to 50) AND (gestational age 36 weeks or more) AND (pregnant) AND (women))"}
{"candidate_id": "LLM04489", "doc_id": "NCT03335904_exc", "case_bucket": "other", "source_criterion": "history of hypertension known impaired renal function liver disease heart failure myocardial infarction coronary artery disease smoked within the past year apnea hypopnea index > 5 events per hour", "candidate_expression": "((apnea hypopnea index > 5 events per hour) AND (coronary artery disease) AND (heart failure) AND (hypertension history) AND (impaired renal function) AND (liver disease) AND (myocardial infarction) AND (smoked within the past year))"}
{"candidate_id": "LLM04490", "doc_id": "NCT02783859_inc", "case_bucket": "or", "source_criterion": "Hospitalised children aged 3-mo to 5-yrs (in Darwin, children have to be Indigenous) Have features of severe pneumonia on admission (temperature >37.5 celsius or a history of fever at home or observed at the referring clinic, age-adjusted tachypnoea [respiratory rate>50 if <12-months; respiratory rate>40 if >12-months] with chest wall recession and/or oxygen saturation <92% in air), and consolidation on chest X-ray as diagnosed by treating clinician After 1-3 days of IV antibiotics, are afebrile, with improved respiratory symptoms and signs, oxygen saturation>90% in air and are ready to be switched to oral amoxicillin-clavulanate, and Have symptoms of no longer than 7 days at point of hospitalisation.", "candidate_expression": "((Hospitalised) AND (age <12-months) AND (age >12-months) AND (aged 3-mo to 5-yrs) AND (chest X-ray) AND (chest wall recession) AND (children) AND (consolidation) AND (oxygen saturation <92% in air) AND (pneumonia severe) AND (respiratory rate >40) AND (respiratory rate >50) AND (symptoms no longer than 7 days at point of hospitalisation) AND (tachypnoea) AND (temperature >37.5 celsius))"}
{"candidate_id": "LLM04491", "doc_id": "NCT01320579_exc", "case_bucket": "or", "source_criterion": "History of other significant skin disease, or skin manifestations of allergic illness or other dermatologic condition, except chronic moderate or severe atopic dermatitis, that would interfere with the trial assessments or compromise the patient's safety according to the opinion of the Investigator Present symptoms of other skin diseases, except chronic atopic dermatitis, that could disturb the study assessment and evaluation of the skin Current use of any active systemic medication for chronic atopic dermatitis within one month Current use of active topical medication in the planned investigational area for chronic atopic dermatitis within two weeks History of a sunny holiday, UV-light therapy or solarium use within one month before beginning of study treatments, or planning such during the study or within 7 days after the study Allergy to cis-UCA, or any constituents of the placebo emulsion cream or any constituents of Protopic® ointment History of any skin-related cancer Congenital or acquired immunodeficiency or ongoing therapy that cause immunosuppression Earlier participation in a clinical study performed with cis-UCA Any clinically significant laboratory test result Suspected current drug or alcohol abuse Clinically significant illness during the 4 weeks prior to the first dose administration Any other condition that in the opinion of the Investigator would interfere with the evaluation of the study results or constitute a health hazard for the patient Unwillingness or doubtful capacity to comply with the protocol Doubtful availability to complete the study", "candidate_expression": "((Allergy) AND (Any clinically significant laboratory test result) AND (Any other condition that in the opinion of the Investigator would interfere with the evaluation of the study results or constitute a health hazard for the patient) AND (Clinically significant illness during the 4 weeks prior to the first dose administration) AND (Doubtful availability to complete the study) AND (History) AND (Unwillingness or doubtful capacity to comply with the protocol) AND (beginning of study treatments) AND (chronic atopic dermatitis within one month) AND (chronic atopic dermatitis within two weeks) AND (illness Clinically significant during the 4 weeks prior to the first dose administration) AND (immunosuppression) AND (laboratory test clinically significant) AND (skin diseases could disturb the study assessment and evaluation of the skin) AND (skin-related cancer) AND (systemic medication active) AND (topical medication active) AND (would interfere with the trial assessments or compromise the patient's safety according to the opinion of the Investigator) AND NOT (chronic atopic dermatitis) AND NOT (atopic dermatitis) AND ((skin disease significant) OR (skin manifestations)) AND ((chronic moderate) OR (severe)) AND ((UV-light therapy) OR (solarium use) OR (sunny holiday)) AND ((during the study) OR (within 7 days after the study)) AND ((Protopic® ointment) OR (cis-UCA) OR (placebo emulsion cream)) AND ((allergic illness) OR (dermatologic condition)) AND ((acquired immunodeficiency) OR (immunodeficiency Congenital) OR (therapy that cause immunosuppression ongoing that cause immunosuppression)) AND ((alcohol abuse) OR (drug abuse)))"}
{"candidate_id": "LLM04492", "doc_id": "NCT02885909_exc", "case_bucket": "other", "source_criterion": "incooperative for glucose monitor refusal of insulin pregnancy", "candidate_expression": "((glucose monitor) AND (incooperative) AND (insulin) AND (pregnancy) AND (refusal))"}
{"candidate_id": "LLM04493", "doc_id": "NCT00319748_inc", "case_bucket": "or", "source_criterion": "Adequate performance status: Breast - Karnofsky score > 50; Ovarian, endometrial or cervical - Gynecologic Oncology Group (GOG) performance score ≤2 If female and of childbearing potential, are willing to use adequate contraception (hormonal, barrier method, abstinence) prior to study entry and for the duration of study participation. Normal organ function within 14 days of study entry Diagnosis of one of the following malignancies: Metastatic breast cancer (BR) Metastatic ovarian cancer (OV) Metastatic endometrial cancer (EM) Metastatic cervical cancer (CX) Measurable metastatic disease (>1cm) in at least one site other than bone-only Progression on or failure to respond to at least one previous chemotherapy regimen for metastatic disease Progression on prior therapy with a hormonal agent if estrogen receptor or progesterone receptor positive, and/or with trastuzumab if HER2-neu positive. If patient has progressed through hormone or trastuzumab therapy only, must have received one chemotherapy regimen. Measurable metastatic disease as defined by Response Evaluation Criteria in Solid Tumors (RECIST) Primary tumor must have been diagnosed histologically as either epithelial ovarian cancer, fallopian tube cancer, or primary peritoneal cancer (not borderline or low malignant potential epithelial carcinoma). Subjects must have failed at least two previous chemotherapy regimens. Paclitaxel must have been a component of one or both regimens and cisplatin or carboplatin must have been a component of one or both regimens. Measurable metastatic disease Histologically proven recurrent or persistent endometrial cancer that is not amenable to curative treatment with surgery and/or radiation therapy AND has failed 2 previous treatment regimens Measurable metastatic disease Histologically proven recurrent or persistent squamous cell carcinoma, adenosquamous carcinoma, or adenocarcinoma of the cervix that is not amenable to curative treatment with surgery and/or radiation therapy AND has failed 2 previous treatment regimens.", "candidate_expression": "((2) AND (> 50) AND (>1cm) AND (Adequate) AND (Breast - Karnofsky score) AND (Gynecologic Oncology Group (GOG) performance score) AND (HER2-neu positive) AND (Histologically) AND (Measurable) AND (Metastatic breast cancer) AND (Metastatic cervical cancer) AND (Metastatic endometrial cancer) AND (Metastatic ovarian cancer) AND (Normal organ function) AND (Ovarian) AND (Paclitaxel) AND (Primary tumor) AND (Progression on) AND (Response Evaluation Criteria in Solid Tumors (RECIST)) AND (abstinence) AND (adenocarcinoma of the cervix) AND (adenosquamous carcinoma) AND (amenable to curative treatment) AND (at least one) AND (at least two) AND (barrier method) AND (borderline) AND (carboplatin) AND (cervical) AND (chemotherapy regimen) AND (chemotherapy regimens) AND (childbearing potential) AND (cisplatin) AND (contraception) AND (endometrial) AND (endometrial cancer) AND (epithelial carcinoma) AND (epithelial ovarian cancer) AND (estrogen receptor positive) AND (failed) AND (failure to respond) AND (fallopian tube cancer) AND (female) AND (for the duration of study participation) AND (histologically) AND (hormonal) AND (hormone therapy) AND (low malignant potential) AND (metastatic disease) AND (not) AND (performance status) AND (persistent) AND (previous) AND (primary peritoneal cancer) AND (prior) AND (prior to study entry) AND (progesterone receptor positive) AND (progressed through) AND (proven) AND (radiation therapy) AND (recurrent) AND (site other than bone-only) AND (squamous cell carcinoma) AND (study entry) AND (study participation) AND (surgery) AND (therapy with a hormonal agent) AND (therapy with trastuzumab) AND (trastuzumab therapy) AND (treatment regimens) AND (willing to) AND (within 14 days of study entry) AND (≤2))"}
{"candidate_id": "LLM04494", "doc_id": "NCT03404804_exc", "case_bucket": "or", "source_criterion": "Children will be excluded if they have a history of developmental delay or inability to communicate the effects of an allergic reaction (non-verbal). Any contraindication to allergy testing will also result in exclusion (i.e. history of a severe allergic reaction to skin tests,, anaphylaxis in the past six weeks, pregnancy, child took any antihistamine in the past three days [including diphenhydramine (Benadryl®), cetirizine (Zyrtec®), loratadine (Claritin®), fexofenadine (Allegra®), levocetirizine (Xyzal®), and desloratadine (Clarinex®)] or child has a history of a condition that requires a beta blocker medicine for cardiac conditions, high blood pressure, migraine headaches, or eye drops for glaucoma (e.g. propranolol, metoprolol, atenolol and Timoptic®, or Betoptic® eye drops). Children who present to the PED with a rash, vomiting or current asthma symptoms including coughing, wheezing or breathing problems will also be excluded to ensure these do not mask reactions to an oral challenge. Patients being admitted to the hospital or those who are deemed too acutely ill for participation (triage level 1 or 2 or as determined by the ED patient care team) will be excluded from the study. During this pilot study, we will exclude non-English speaking families. However, in subsequent studies we will include the non-English speaking population. Children who are wards of the state, in foster care or police custody or detention will be excluded. Children with any basal condition (trauma, infection, minor accidents, etc..) will be able to participate in the study provided they and their family are willing and do not meet the above-mentioned exclusion criteria.", "candidate_expression": "((Allegra) AND (Benadryl) AND (Betoptic) AND (Children) AND (Clarinex) AND (Claritin) AND (PED) AND (Timoptic) AND (Xyzal) AND (Zyrtec) AND (allergic reaction) AND (allergy testing) AND (anaphylaxis) AND (antihistamine) AND (asthma symptoms) AND (atenolol) AND (basal condition) AND (beta blocker medicine) AND (breathing problems) AND (cardiac conditions) AND (cetirizine) AND (contraindication) AND (coughing) AND (current) AND (desloratadine) AND (detention) AND (developmental delay) AND (diphenhydramine) AND (eye drops) AND (fexofenadine) AND (foster care) AND (glaucoma) AND (high blood pressure) AND (history) AND (in the past six weeks) AND (in the past three days) AND (inability to communicate the effects) AND (infection) AND (levocetirizine) AND (loratadine) AND (metoprolol) AND (migraine headaches) AND (minor accidents) AND (non-English speaking) AND (non-verbal) AND (police custody) AND (pregnancy) AND (propranolol) AND (rash) AND (severe allergic reaction) AND (skin tests) AND (trauma) AND (vomiting) AND (wards of the state) AND (wheezing))"}
{"candidate_id": "LLM04495", "doc_id": "NCT02780427_inc", "case_bucket": "other", "source_criterion": "Children, aged between one and 24 months. classified as (American Society of Anesthesiologists) ASA physical status I or II, undergoing TEE were enrolled in the study.", "candidate_expression": "((ASA physical status) AND (American Society of Anesthesiologists) AND (Children) AND (I or II) AND (TEE) AND (aged) AND (between one and 24 months))"}
{"candidate_id": "LLM04496", "doc_id": "NCT03073603_exc", "case_bucket": "or", "source_criterion": "Any MS relapse in the last five years, as determined at the screen visit by the PI Any new or definitely enlarging T2/FLAIR lesion or new gadolinium-enhancing lesion within the past three years (at least two scans separated by at least three years must be reviewed) on brain or spine MRI scan. Lesions must be 3mm or larger to be exclusionary. Significant (as defined by the PI) intolerance of presently-used DMT Use of inhaled or topical steroids are not an exclusion criteria. Use of oral steroids for no greater than 14 days given for a non-MS condition is not exclusionary. alemtuzumab, mitoxantrone, cyclophosphamide, methotrexate, cyclosporine, or rituximab Prior use of any experimental agent used as a DMT for MS in the last five years uncontrolled hypertension, uncontrolled diabetes, uncontrolled asthma, or uncontrolled depression Cancers other than basal cell skin cancers within the last 5 years Unable to give informed consent or follow the protocol Unable to undergo brain MRI Unwilling to be randomized per this protocol History of other chronic neurological illnesses that might mimic MS with chronic or intermittent symptoms (i.e. ALS, myasthenia gravis, chronic neuropathy, etc.)", "candidate_expression": "((Cancers) AND (DMT presently-used) AND (Lesions 3mm or larger) AND (MS) AND (Unwilling to be randomized per this protocol) AND (alemtuzumab) AND (asthma uncontrolled) AND (brain MRI Unable to undergo) AND (chronic neurological illnesses mimic MS) AND (cyclophosphamide) AND (cyclosporine) AND (depression uncontrolled) AND (diabetes uncontrolled) AND (gadolinium) AND (hypertension uncontrolled) AND (intolerance Significant) AND (methotrexate) AND (mitoxantrone) AND (non-MS condition) AND (not) AND (relapse in the last five years) AND (rituximab) AND (scans at least two separated by at least three years) AND NOT (oral steroids no greater than 14 days) AND NOT (basal cell skin cancers within the last 5 years) AND ((brain MRI scan) OR (spine MRI scan)) AND ((inhaled steroids) OR (topical steroids)) AND ((T2/FLAIR lesion) OR (lesion gadolinium-enhancing)) AND ((ALS) OR (chronic neuropathy) OR (myasthenia gravis)))"}
{"candidate_id": "LLM04497", "doc_id": "NCT02550028_exc", "case_bucket": "or", "source_criterion": "Babies who have been close to death Seizure occurred by metabolic factors (hypoglycemia, hypocalcemia, electrolyte disorder) Babies who have received phenobarbitone or any other anticonvulsive medication before hospitalization Abnormal renal function", "candidate_expression": "((Abnormal renal function) AND (Babies) AND (Seizure metabolic factors) AND (close to death have been) AND (hospitalization) AND (renal function Abnormal) AND ((anticonvulsive medication any other) OR (phenobarbitone)) AND ((electrolyte disorder) OR (hypocalcemia) OR (hypoglycemia)))"}
{"candidate_id": "LLM04498", "doc_id": "NCT03537924_exc", "case_bucket": "or", "source_criterion": "Any active respiratory, cardiovascular or other disease requiring regular treatment or being otherwise relevant for tolerance of hypoxia or altitude exposure. Any condition that may interfere with protocol compliance including current heavy smoking (>20 cigarettes per day or >20 pack-years with active smoking during the last 10 years), regular use of alcohol. Allergy to acetazolamide and other sulfonamides.", "candidate_expression": "((>20) AND (Allergy) AND (active) AND (active smoking) AND (cigarettes per day) AND (during the last 10 years) AND (other) AND (pack-years) AND (relevant being) AND (requiring) AND (tolerance) AND (treatment) AND ((altitude exposure) OR (hypoxia)) AND ((heavy smoking) OR (regular use of alcohol)) AND ((acetazolamide) OR (sulfonamides)) AND ((cardiovascular disease) OR (disease) OR (respiratory disease)))"}
{"candidate_id": "LLM04499", "doc_id": "NCT02570230_inc", "case_bucket": "other", "source_criterion": "ASA physical status 1-3 elective thoracotomy can operate patient-controlled analgesia (PCA) machine", "candidate_expression": "((1-3) AND (ASA physical status) AND (elective) AND (thoracotomy))"}
{"candidate_id": "LLM04500", "doc_id": "NCT01614041_inc", "case_bucket": "or", "source_criterion": "18-65 years old Male or female Diagnosed with GAD according to DSM-IV HAMA score=17 Provide with written informed consent Agree to be washed-out for two weeks if receiving SSRI, SNRI or NASA.", "candidate_expression": "((18-65) AND (=17) AND (DSM-IV) AND (GAD) AND (HAMA score) AND (Male) AND (NASA) AND (Provide with written informed consent) AND (SNRI) AND (SSRI) AND (female) AND (for two weeks) AND (washed-out) AND (years old))"}
```
