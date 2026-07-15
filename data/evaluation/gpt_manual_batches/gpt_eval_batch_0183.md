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
{"candidate_id": "LLM04551", "doc_id": "NCT02283996_inc", "case_bucket": "other", "source_criterion": "Patient must be 18 years or older Must meet the following definition for adhesive capsulitis as defined by the American Academy of Orthopedic Surgeons: Self-limiting condition resulting from any inflammatory process about the shoulder in which capsular scar tissue is produced, resulting in pain and limited range of motion; also called frozen shoulder Must be amenable to randomization into either cohort", "candidate_expression": "((18 or older) AND (American Academy of Orthopedic Surgeons) AND (Must be amenable to randomization into either cohort) AND (adhesive capsulitis) AND (years))"}
{"candidate_id": "LLM04552", "doc_id": "NCT03088904_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04553", "doc_id": "NCT03056287_exc", "case_bucket": "or", "source_criterion": "1. Unable to ambulate at least 150 feet prior to stroke, or experienced intermittent claudication while walking; 2. history of congestive heart failure, unstable cardiac arrhythmias, hypertrophic cardiomyopathy, severe aortic stenosis, angina or dyspnea at rest or during ADL's; 3. History of oxygen dependence; 4. Preexisting neurological disorders, dementia or previous stroke; 5. History of major head trauma; 6. Legal blindness or severe visual impairment; 7. history of psychosis or other Axis I disorder that is primary; 8. Life expectancy <1 yr.; 9. Severe arthritis or other problems that limit passive range of motion; 10. History of DVT or pulmonary embolism within 6 months; 11. Uncontrolled diabetes with recent weight loss, diabetic coma, or frequent insulin reactions; 12. Severe hypertension with systolic >200 mmHg and diastolic >110 mmHg at rest; 13. attempt of suicide in the last 2 years or at suicidal risk assessed by SCID interview; 14. Previous or current enrollment in a clinical trial to enhance motor recovery; 15) currently exercising ≥ 2 times per week (≥20 minutes); 16) Presence of non-MR compatible implants, pregnancy or severe claustrophobia.", "candidate_expression": "((<1 yr) AND (>110 mmHg) AND (>200 mmHg) AND (Axis I disorder) AND (DVT) AND (History) AND (Legal blindness) AND (Life expectancy) AND (Preexisting) AND (SCID interview) AND (Severe arthritis) AND (Severe hypertension) AND (Unable to ambulate at least 150 feet) AND (Uncontrolled) AND (angina) AND (at suicidal risk) AND (attempt of suicide) AND (claustrophobia) AND (congestive heart failure) AND (dementia) AND (diabetes) AND (diabetic coma) AND (diastolic) AND (dyspnea at rest) AND (dyspnea during ADL's) AND (frequent) AND (history) AND (hypertrophic cardiomyopathy) AND (in the last 2 years) AND (insulin reactions) AND (intermittent claudication) AND (major head trauma) AND (neurological disorders) AND (non-MR compatible implants) AND (oxygen dependence) AND (pregnancy) AND (previous) AND (primary) AND (prior) AND (problems that limit passive range of motion) AND (psychosis) AND (pulmonary embolism) AND (severe) AND (severe aortic stenosis) AND (severe visual impairment) AND (stroke) AND (systolic) AND (unstable cardiac arrhythmias) AND (weight loss) AND (while walking) AND (within 6 months))"}
{"candidate_id": "LLM04554", "doc_id": "NCT02055053_inc", "case_bucket": "or", "source_criterion": "Age 18 or older with unilateral or bilateral inguinal herna for laparoscopic repair American Society of Anesthesiology (ASA) Class I and II", "candidate_expression": "((18 or older) AND (Age) AND (American Society of Anesthesiology (ASA) Class) AND (I and II) AND (for laparoscopic repair) AND (inguinal herna) AND (laparoscopic repair) AND ((bilateral) OR (unilateral)))"}
{"candidate_id": "LLM04555", "doc_id": "NCT01715584_exc", "case_bucket": "or", "source_criterion": "patient refusal age less than 40 or over 80 years combined surgical procedures emergency surgery Left ventricular ejection fraction less than 50 per cent calculated creatinine clearance less than 60 mL per minute", "candidate_expression": "((Left ventricular ejection fraction less than 50 per cent) AND (age less than 40 over 80 years) AND (calculated creatinine clearance less than 60 mL per minute) AND (combined surgical procedures) AND (emergency surgery) AND (patient refusal))"}
{"candidate_id": "LLM04556", "doc_id": "NCT02590653_inc", "case_bucket": "other", "source_criterion": "Signed Informed Consent Form Patients having physical and mental ability to participate in the study Patients of both sexes aged 35 to 65 years Presence of documented ST-elevation myocardial infarction confirmed by ECG, as well as troponin I and CK-MB levels. Presence of hemodynamically relevant stenosis of one artery (i.e., the infarct-related artery) confirmed by coronary angiography (CAG), with the occlusion of other arteries not exceeding 30%.", "candidate_expression": "((CAG) AND (CK-MB) AND (ECG) AND (Patients having physical and mental ability to participate in the study) AND (ST-elevation myocardial infarction) AND (Signed Informed Consent Form) AND (aged 35 to 65 years) AND (coronary angiography) AND (infarct-related artery) AND (occlusion of other arteries not exceeding 30%) AND (sexes both) AND (stenosis of artery hemodynamically relevant one) AND (troponin I))"}
{"candidate_id": "LLM04557", "doc_id": "NCT01717911_inc", "case_bucket": "other", "source_criterion": "Recently diagnosed type 2 diabetic patients. Fasting plasma glucose between 200-300 mg/dl (A1C level between 7% and 10%). Those who age between 30 and 80 years old and can inject insulin by themselves.", "candidate_expression": "((A1C level) AND (Fasting plasma glucose) AND (Recently diagnosed) AND (age) AND (between 200-300 mg/dl) AND (between 30 and 80 years old) AND (between 7% and 10%) AND (can) AND (inject insulin) AND (type 2 diabetic))"}
{"candidate_id": "LLM04558", "doc_id": "NCT03223909_exc", "case_bucket": "or", "source_criterion": "Subjects with topical and/or systemic medication or mechanical devices that interfere determinedly on the results of the study (such as topical immunomodulators, punctal plugs, corticosteroids, preservative artificial tears, contact lenses). Subjects (females) with active sexual life that do not use a contraceptive method. Female subjects who are pregnant or lactating Female subjects with a positive urine pregnancy test Positive drug addictions* (verbal interrogatory) Subjects who have participated on any other research clinical trials on the last 40 days Subjects legal or mentally disabled to give an informed consent for participating on this study Subjects who can't comply with the appointments or with every protocol requirement. Serious tear film dysfunction syndrome TBUT < 5 s Schirmer: < 4 mm OSDI > 30 pints Corneal staining > grade III on the Oxford scale Non perforated corneal ulcer Perforated corneal ulcer Autoimmune corneal ulcer Ocular surface scarring diseases Ocular surface or annexes metaplastic lesions Fibro vascular proliferation lesions on the conjunctival and/or corneal surface (i.e.: pterygium) Concomitant chronic inflammatory diseases on any ocular structure Acute or infectious inflammatory disease Corneal disease potentially requiring a treatment during the following 3 months Use of topical or systemic drug products classified as forbidden Ocular surgical procedures 3 months before the protocol inclusion Treatments or procedures indicated on the tear film dysfunction treatment, as punctal silicone plugs. Posterior segment diseases requiring a treatment or threatening the visual prognosis Retinal diseases potentially requiring treatment during the following 3 months History of penetrating keratoplasty. Soft or hard contact lenses use during the last month from inclusion day", "candidate_expression": "((3 months before the protocol inclusion) AND (< 4 mm) AND (< 5 s) AND (> 30 pints) AND (> grade III) AND (Autoimmune) AND (Concomitant) AND (Corneal disease) AND (Corneal staining) AND (Female) AND (Fibro vascular proliferation lesions) AND (History) AND (Non perforated) AND (OSDI) AND (Ocular surface scarring diseases) AND (Ocular surgical procedures) AND (Oxford scale) AND (Perforated) AND (Positive drug addictions) AND (Posterior segment diseases) AND (Retinal diseases) AND (Schirmer) AND (Serious tear film dysfunction syndrome) AND (Subjects legal or mentally disabled to give an informed consent for participating on this study) AND (Subjects who have participated on any other research clinical trials on the last 40 days) AND (TBUT) AND (active sexual life) AND (chronic inflammatory diseases) AND (contraceptive method) AND (corneal ulcer) AND (during the following 3 months) AND (during the last month from inclusion day) AND (females) AND (inclusion day) AND (inflammatory disease) AND (not) AND (ocular structure) AND (penetrating keratoplasty) AND (positive) AND (potentially requiring) AND (protocol inclusion) AND (pterygium) AND (punctal silicone plugs) AND (requiring) AND (tear film dysfunction treatment) AND (treatment) AND (urine pregnancy test) AND (verbal interrogatory) AND ((lactating) OR (pregnant)) AND ((legal disabled) OR (mentally disabled)) AND ((mechanical devices) OR (systemic medication) OR (topical medication)) AND ((annexes metaplastic lesions Ocular) OR (lesions Ocular surface)) AND ((conjunctival) OR (corneal surface)) AND ((Acute) OR (infectious)) AND ((Treatments) OR (procedures)) AND ((contact lenses) OR (corticosteroids) OR (preservative artificial tears) OR (punctal plugs) OR (topical immunomodulators)) AND ((threatening the visual prognosis) OR (treatment)) AND ((Soft contact lenses) OR (hard contact lenses)))"}
{"candidate_id": "LLM04559", "doc_id": "NCT01391780_exc", "case_bucket": "or", "source_criterion": "neurological diseases previous pelvic surgeries diabetes cognitive difficulties vaginal and urinary infection", "candidate_expression": "((cognitive difficulties) AND (diabetes) AND (infection vaginal) AND (neurological diseases) AND (pelvic surgeries) AND (previous) AND (urinary infection))"}
{"candidate_id": "LLM04560", "doc_id": "NCT03249311_inc", "case_bucket": "other", "source_criterion": "Male participants between 18 and 40 years-old Written informed consent signed by the participant", "candidate_expression": "((Male) AND (Written informed consent signed by the participant) AND (old between 18 and 40 years))"}
{"candidate_id": "LLM04561", "doc_id": "NCT02150590_inc", "case_bucket": "other", "source_criterion": "chronic obstructive pulmonary disease (COPD), GOLD grade 2-3 residents at low altitude (<800 m)", "candidate_expression": "((2-3) AND (COPD) AND (GOLD grade) AND (chronic obstructive pulmonary disease))"}
{"candidate_id": "LLM04562", "doc_id": "NCT02150590_inc", "case_bucket": "other", "source_criterion": "chronic obstructive pulmonary disease (COPD), GOLD grade 2-3 residents at low altitude (<800 m)", "candidate_expression": "((2-3) AND (COPD) AND (GOLD grade) AND (chronic obstructive pulmonary disease))"}
{"candidate_id": "LLM04563", "doc_id": "NCT02742233_inc", "case_bucket": "or", "source_criterion": "Diagnosis of diabetes mellitus according to World Health Organization criteria ( treatment with insulin or an oral hypoglycemic agent, twice random glucose measurements major than 200 mg/dl, or a fasting glucose major than 140 mg/dl) Ulcer located on the legs or feet, stage III or IV (Wagner Classification System) The subject agrees to comply with study protocol requirements and all follow up visit requirements.", "candidate_expression": "((III or IV) AND (The subject agrees to comply with study protocol requirements and all follow up visit requirements) AND (Wagner Classification System) AND (World Health Organization criteria) AND (diabetes mellitus) AND (major than 140 mg/dl) AND (major than 200 mg/dl) AND (twice) AND ((Ulcer) OR (stage)) AND ((feet) OR (legs)) AND ((insulin) OR (oral hypoglycemic agent)) AND ((fasting glucose) OR (random glucose measurements) OR (treatment)))"}
{"candidate_id": "LLM04564", "doc_id": "NCT01116973_exc", "case_bucket": "or", "source_criterion": "Inability to obtain consent Subjects under 18 years of age Non-English speaking subjects Subjects that are unable to lay flat due to pulmonary complications, increased intracranial pressure (ICP), or unstable spinal cord injuries Subjects with known cardiac abnormalities (atrial septal defects or ventricular septal defects, severe tricuspid valve disease, severe pulmonary hypertension, Ejection fraction < 15%) Prisoners Subjects with known upper extremity deep vein thromboses (subclavian or distal) Subjects with non-functional CICC or PICC distal ports Subjects with femoral CICCs Pregnant women", "candidate_expression": "((< 15%) AND (CICC distal ports) AND (Ejection fraction) AND (Inability to obtain consent) AND (PICC distal ports) AND (Pregnant) AND (Prisoners) AND (age) AND (atrial septal defects) AND (cardiac abnormalities) AND (distal) AND (due to pulmonary complications) AND (femoral CICCs) AND (increased intracranial pressure (ICP)) AND (non-functional) AND (pulmonary complications) AND (pulmonary hypertension) AND (severe) AND (spinal cord injuries) AND (subclavian) AND (tricuspid valve disease) AND (unable to lay flat) AND (under 18 years) AND (unstable) AND (upper extremity deep vein thromboses) AND (ventricular septal defects) AND (women))"}
{"candidate_id": "LLM04565", "doc_id": "NCT02145026_inc", "case_bucket": "or", "source_criterion": "Adult participants with low or intermediate-1 risk MDS No previous treatment with hematopoietic growth factors within 3 months prior to screening Symptomatic anemia (hemoglobin <10 g/dL) as determined by investigator Serum erythropoietin <500 milliunits/milliliter (mU/mL) within 14 days prior to the first dose of study treatment Require no red blood cell transfusion or dependent on <4 units within 8 weeks prior to screening Clinically stable for at least 1 month prior to entry into the study For female participants of childbearing potential and male participants with partners of childbearing potential, agreement (by participants and/or partner) to use highly effective form(s) of contraception", "candidate_expression": "((Adult) AND (For female participants of childbearing potential and male participants with partners of childbearing potential, agreement (by participants and/or partner) to use highly effective form(s) of contraception) AND (MDS) AND (Serum erythropoietin <500 milliunits/milliliter within 14 days prior to the first dose of study treatment) AND (anemia Symptomatic) AND (hematopoietic growth factors within 3 months prior to screening) AND (hemoglobin <10 g/dL) AND (stable for at least 1 month prior to entry into the study) AND NOT (red blood cell transfusion <4 units within 8 weeks prior to screening) AND ((intermediate-1 risk) OR (low risk)))"}
{"candidate_id": "LLM04566", "doc_id": "NCT03506477_inc", "case_bucket": "or", "source_criterion": "Provide written, signed and dated informed consent prior to initiating any study-related activities. Male or female >18 years of age at the time of screening Fitzpatrick Skin phototype IV-VI, non-white race/ethnicity, including but not limited to - --African Americans, Asians, Pacific Islanders and Hispanics. Clinical diagnosis of chronic plaque-type psoriasis of the body Plaque psoriasis with =2% Body Surface Area (BSA) involvement (may include scalp involvement), PASI Score = 2, IGA mod 2011 score of 2 or greater (based on scale of 0-4) Females of childbearing potential (FCBP) must have a negative pregnancy test at Screening and Baseline. While using investigational product and for at least 28 days after last application of investigational product, FCBP who engage in activity in which conception is possible must use one of the approved contraceptive options d Must be in general good health as judged by the Investigator, based on medical history and physical examination.", "candidate_expression": "((2 or greater) AND (= 2) AND (=2% Body Surface Area (BSA)) AND (>18 years of age) AND (African Americans) AND (Asians) AND (Females of childbearing potential (FCBP) must have a negative pregnancy test at Screening and Baseline. While using investigational product and for at least 28 days after last application of investigational product, FCBP who engage in activity in which conception is possible must use one of the approved contraceptive options d) AND (Fitzpatrick Skin phototype) AND (Hispanics) AND (IGA mod 2011 score) AND (IV-VI) AND (Male) AND (PASI Score) AND (Pacific Islanders) AND (Plaque psoriasis) AND (Provide written, signed and dated informed consent prior to initiating any study-related activities.) AND (age) AND (at the time of screening) AND (chronic) AND (female) AND (involvement) AND (non-white race/ethnicity) AND (plaque-type) AND (psoriasis of the body) AND (scale of 0-4) AND (the time of screening))"}
{"candidate_id": "LLM04567", "doc_id": "NCT03208244_inc", "case_bucket": "scope", "source_criterion": "Recipient is Age = 18 years Serum ALT within normal limits with no history of liver disease Lack of sensitization (i.e. PRA < 20%) that would be expected to result in a high likelihood of needing aggressive immunosuppression to treat rejection", "candidate_expression": "((Age = 18 years) AND (PRA < 20%) AND (Serum ALT within normal limits) AND (sensitization) AND NOT (liver disease history))"}
{"candidate_id": "LLM04568", "doc_id": "NCT03255044_inc", "case_bucket": "other", "source_criterion": "older than 18 years (of both sexes) diagnosed with stable chronic heart failure NYHA class II-III ejection fraction < 40 % as assessed by 2D echocardiography who have been optimized on Guideline Directed treatment for heart failure for at least a month prior to enrolling.", "candidate_expression": "((2D echocardiography) AND (NYHA class II-III) AND (both sexes) AND (chronic heart failure stable) AND (ejection fraction < 40 %) AND (years older than 18))"}
{"candidate_id": "LLM04569", "doc_id": "NCT03233880_inc", "case_bucket": "other", "source_criterion": "primigravida, singleton pregnancy, maternal age 18-35 years, and pregnancy duration 16-20 weeks at the time of study inclusion.", "candidate_expression": "((16-20 weeks) AND (18-35 years) AND (at the time of study inclusion) AND (maternal age) AND (pregnancy duration) AND (primigravida) AND (singleton pregnancy))"}
{"candidate_id": "LLM04570", "doc_id": "NCT02958072_inc", "case_bucket": "or", "source_criterion": "Diabetes mellitus Foot ulcer at the malleoli area between 0,25 cm² and 5,0 cm² Foot ulcer duration more than 6 weeks Ankle-brachial index above 0,40 or presence of palpable pulses in arteria dorsalis pedes and/or arteria tibialis posterior informed consent", "candidate_expression": "((Ankle-brachial index above 0,40) AND (Diabetes mellitus) AND (Foot ulcer malleoli area between 0,25 cm² and 5,0 cm²) AND (Foot ulcer more than 6 weeks) AND (informed consent) AND (palpable pulses arteria dorsalis pedes arteria tibialis posterior))"}
{"candidate_id": "LLM04571", "doc_id": "NCT00846703_exc", "case_bucket": "other", "source_criterion": "No Down syndrome No other major disease that prohibits study treatment (e.g., severe congenital heart disease) Not requiring significant therapy modification owing to study therapy associated complications No complications due to other interventions No one with missing data that are needed for the differential diagnosis, or for selection of the proper therapy arm", "candidate_expression": "((Down syndrome) AND (No) AND (Not) AND (complications) AND (congenital heart disease) AND (interventions) AND (major disease) AND (other) AND (severe) AND (study therapy))"}
{"candidate_id": "LLM04572", "doc_id": "NCT01531257_exc", "case_bucket": "or", "source_criterion": "1. Need for combined organ transplantation with an extra-renal organ and/or islet cell transplant. 2. Recipients of previous non-renal solid organ and/or islet cell transplantation. 3. Infection with HIV. 4. Inability or unwillingness of a participant and/or guardian to provide informed consent", "candidate_expression": "((Inability or unwillingness of a participant and/or guardian to provide informed consent) AND (Infection with HIV) AND (combined organ transplantation extra-renal organ) AND (islet cell transplant) AND (islet cell transplantation) AND (non-renal solid organ transplantation))"}
{"candidate_id": "LLM04573", "doc_id": "NCT02571179_exc", "case_bucket": "or", "source_criterion": "a disease that might affect hepatic or renal function, contraindications to opioid analgesics, fetal growth retardation, signs of fetal asphyxia by cardiotocography, meconium stained amniotic fluid or placental insufficiency. The subjects should not have received fentanyl during the previous 14 days.", "candidate_expression": "((affect hepatic function) AND (affect renal function) AND (cardiotocography) AND (contraindications) AND (disease) AND (during the previous 14 days) AND (fentanyl) AND (fetal asphyxia) AND (fetal growth retardation) AND (meconium stained amniotic fluid) AND (not) AND (opioid analgesics) AND (placental insufficiency) AND (signs of))"}
{"candidate_id": "LLM04574", "doc_id": "NCT03460002_exc", "case_bucket": "or", "source_criterion": "the child has temperature > 39.0◦C or a severe acute illness as defined by the examining nurse the child has as a mid upper arm circumference < 110 mm and is older than 6 months (most feasible local indicator of AIDS and chronic immunosuppressive disease) the child has experienced a severe allergic reaction after previous vaccination, drug or food. the child is enrolled in an ongoing study of Bacillus Calmette Guerin vaccine and is < 2 months old For the RECAMP-MV trial: the child is enrolled in RECAMP-OPV", "candidate_expression": "((< 110 mm) AND (> 39.0◦C) AND (RECAMP-MV trial) AND (acute illness) AND (after previous vaccination, drug or food) AND (as defined by the examining nurse) AND (child) AND (drug) AND (enrolled in RECAMP-OPV) AND (food) AND (is older than 6 months) AND (mid upper arm circumference) AND (old) AND (previous) AND (previous vaccination, drug or food) AND (severe) AND (severe allergic reaction) AND (temperature) AND (the child is enrolled in an ongoing study of Bacillus Calmette Guerin vaccine and is < 2 months old) AND (vaccination))"}
{"candidate_id": "LLM04575", "doc_id": "NCT03120533_exc", "case_bucket": "or", "source_criterion": "Healthy Volunteers Treprostinil contraindications: Known hypersensitivity to treprostinil or any of the excipients, Pulmonary arterial hypertension related to veno-occlusive disease, Congestive heart failure due to severe left ventricular dysfunction, Severe hepatic insufficiency (Child-Pugh stage C), Evolving gastrointestinal ulcer, intracranial hemorrhage, recent trauma or other clinical condition that may lead to bleeding, Congenital or acquired valvular abnormalities with cardiac repercussions, Severe ischemic heart disease or unstable angina; Myocardial infarction in the last six months; Decompensated cardiac insufficiency not medically controlled; Severe arrhythmias; Cerebrovascular lesions (such as transient ischemic attack, stroke) that occurred within the last three months. Persons referred to in Articles L1121-5 to L1121-8 of the French Public health Code: pregnant woman, parturient, nursing mother, person deprived of liberty by judicial or administrative decision, person subject to a legal protection measure, can not Be included in clinical trials. Subject in an exclusion period from another study, Subject who would receive more than 4500 euros of compensation due to his participation in other biomedical research in the 12 months preceding this study Systemic sclerosis patients: Iloprost cure carried out in the previous month or planned in the following month. Initiation or change of dosage of bosentan, sildenafil or calcium channel blockers in the previous month or in the following month Digital Sympathectomy or botulinum toxin injection planned in the following month. Clinically superinfected digital ulcers Treprostinil contraindications: Known hypersensitivity to treprostinil or any of the excipients, Pulmonary arterial hypertension related to veno-occlusive disease, Congestive heart failure due to severe left ventricular dysfunction, Severe hepatic insufficiency (Child-Pugh stage C), Evolving gastrointestinal ulcer, intracranial hemorrhage, recent trauma or other clinical condition that may lead to bleeding, Congenital or acquired valvular abnormalities with cardiac repercussions, Severe ischemic heart disease or unstable angina; Myocardial infarction in the last six months; Decompensated cardiac insufficiency not medically controlled; Severe arrhythmias; Cerebrovascular lesions (such as transient ischemic attack, stroke) that occurred within the last three months. Persons referred to in Articles L1121-5 to L1121-8 of the French Public health Code: pregnant woman, parturient, nursing mother, person deprived of liberty by judicial or administrative decision, person subject to a legal protection measure, can not Be included in clinical trials. Subject in an exclusion period from another study, Subject who would receive more than 4500 euros of compensation due to his participation in other biomedical research in the 12 months preceding this study", "candidate_expression": "((Cerebrovascular lesions within the last three months) AND (Child-Pugh stage C) AND (Congenital valvular abnormalities with cardiac repercussions) AND (Congestive heart failure) AND (Decompensated cardiac insufficiency) AND (Decompensated cardiac insufficiency not medically controlled) AND (Digital Sympathectomy) AND (Iloprost in the previous month) AND (Iloprost planned in the following month) AND (Myocardial infarction in the last six months) AND (Pulmonary arterial hypertension) AND (Systemic sclerosis) AND (Treprostinil) AND (acquired valvular abnormalities with cardiac repercussions) AND (any of the excipients) AND (arrhythmias Severe) AND (bosentan) AND (botulinum toxin injection) AND (calcium channel blockers in the previous month in the following month) AND (clinical condition that may lead to bleeding) AND (contraindications) AND (deprived of liberty) AND (digital ulcers superinfected) AND (gastrointestinal ulcer) AND (gastrointestinal ulcer Evolving) AND (hepatic insufficiency Severe) AND (hypersensitivity) AND (intracranial hemorrhage) AND (ischemic heart disease Severe) AND (left ventricular dysfunction severe) AND (nursing) AND (parturient) AND (pregnant) AND (sildenafil) AND (stroke) AND (subject to a legal protection) AND (transient ischemic attack) AND (trauma recent) AND (treprostinil) AND (unstable angina) AND (veno-occlusive disease) AND (woman))"}
```
