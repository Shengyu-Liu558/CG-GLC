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
{"candidate_id": "LLM06526", "doc_id": "NCT02478515_exc", "case_bucket": "or", "source_criterion": "Previous treatment with anti-VEGF drugs or corticosteroid or grid laser photocoagulation (study eye) History of vitrectomy surgery, submacular surgery, or other surgical intervention for RVO Ocular disorders in the study eye that may confound interpretation of study results BCVA over 77 letters between screening and Day 0 The pregnant or lactating woman", "candidate_expression": "((BCVA) AND (RVO) AND (The pregnant or lactating woman) AND (over 77 letters) AND ((anti-VEGF drugs) OR (corticosteroid) OR (grid laser photocoagulation ()) AND ((submacular surgery) OR (surgical intervention) OR (vitrectomy surgery)))"}
{"candidate_id": "LLM06527", "doc_id": "NCT02375295_exc", "case_bucket": "other", "source_criterion": "Patients with medical comorbidities preventing them from definitive surgical therapy. Patients with persistent stone burden following definitive surgical therapy.", "candidate_expression": "((definitive surgical therapy) AND (following definitive surgical therapy) AND (medical comorbidities) AND (persistent) AND (preventing them from) AND (stone burden))"}
{"candidate_id": "LLM06528", "doc_id": "NCT02816164_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed primary breast cancer Planned to start docetaxel component of FEC-D or AC-D, or first cycle of; dose-dense AC-T, TC, FEC-D or TAC chemotherapy =19 years of age Able to provide verbal consent", "candidate_expression": "((AC-D first cycle of) AND (Able to provide verbal consent) AND (FEC-D) AND (Histologically) AND (TAC chemotherapy) AND (TC) AND (age =19 years) AND (docetaxel) AND (dose-dense AC-T) AND (primary breast cancer Histologically confirmed))"}
{"candidate_id": "LLM06529", "doc_id": "NCT03464552_inc", "case_bucket": "other", "source_criterion": "Females 18-65 years old who undergoing colposcopic directed biopsy", "candidate_expression": "((18-65 years) AND (Females) AND (colposcopic directed biopsy) AND (old) AND (undergoing))"}
{"candidate_id": "LLM06530", "doc_id": "NCT02701881_exc", "case_bucket": "or", "source_criterion": "Acute critical limb ischemia Severe critical limb ischemia (Rutherford category 6) Major bleeding history within prior 2 months Known hypersensitivity or contraindication to any of the following medications: heparin, aspirin, clopidogrel or contrast agents Age > 85 years Severe hepatic dysfunction (> 3 times normal reference values) Significant renal dysfunction (Serum creatinine > 2.0 mg/dl Significant leucopenia, neutropenia, thrombocytopenia, anemia, or known bleeding diathesis LVEF <40% or clinically overt congestive heart failure Pregnant women or women with potential childbearing Life expectancy <1 year due to comorbidity Previous bypass surgery or stenting of the superficial femoral artery Untreated inflow disease of the ipsilateral pelvic arteries (more than 50%stenosis or or occlusion Popliteal artery stenosis >50% at P2 or P3 segment", "candidate_expression": "((6) AND (<1 year) AND (<40%) AND (> 2.0 mg/dl) AND (> 85 years) AND (>50%) AND (Acute) AND (Age) AND (LVEF) AND (Life expectancy) AND (Major bleeding history) AND (P2 or P3 segment) AND (Popliteal artery stenosis) AND (Pregnant) AND (Previous) AND (Rutherford category) AND (Serum creatinine) AND (Severe) AND (Significant) AND (Untreated) AND (anemia) AND (aspirin) AND (bleeding diathesis) AND (bypass surgery) AND (clinically overt) AND (clopidogrel) AND (comorbidity) AND (congestive heart failure) AND (contraindication) AND (contrast agents) AND (critical) AND (heparin) AND (hepatic dysfunction) AND (hypersensitivity) AND (inflow disease) AND (ipsilateral pelvic arteries) AND (leucopenia) AND (limb ischemia) AND (more than 50%) AND (neutropenia) AND (occlusion) AND (potential childbearing) AND (renal dysfunction) AND (stenosis) AND (stenting of the superficial femoral artery) AND (thrombocytopenia) AND (within prior 2 months) AND (women))"}
{"candidate_id": "LLM06531", "doc_id": "NCT03356834_exc", "case_bucket": "or", "source_criterion": "Co-infected with HCV, HIV or other viral hepatitis, Diagnosis of HCC", "candidate_expression": "((Co-infected) AND (HCC) AND (other) AND ((HCV) OR (HIV) OR (viral hepatitis)))"}
{"candidate_id": "LLM06532", "doc_id": "NCT02923700_inc", "case_bucket": "or", "source_criterion": "patients affected by mono-lateral symptomatic knee articular degenerative pathology with history of chronic (for at least 4 months) pain or swelling; imaging findings of degenerative changes of the joint (osteoarthritis or chondropathy with Kellgren Lawrence Score from 0 to 3 at X-ray evaluation).", "candidate_expression": "((Kellgren Lawrence Score from 0 to 3) AND (X-ray) AND (chondropathy) AND (degenerative changes) AND (imaging) AND (knee articular degenerative pathology mono-lateral symptomatic for at least 4 months) AND (osteoarthritis) AND (pain) AND (swelling))"}
{"candidate_id": "LLM06533", "doc_id": "NCT03495609_exc", "case_bucket": "or", "source_criterion": "History of allergic reaction to compounds of similar chemical or biologic composition to hCG receiving medication that could interfere with the study protocol objectives (hormonal contraceptives, androgens, prednisone, thyroid hormones, insulin) previous treatment with follicle stimulating hormone for assisted reproduction uncontrolled intercurrent illness Heart disease Severe cognitive decline Psychiatric desease HIV positive Hepatitis B or C infection", "candidate_expression": "((HIV positive) AND (Heart disease) AND (Hepatitis B infection) AND (Hepatitis C infection) AND (History) AND (Psychiatric desease) AND (Severe) AND (allergic reaction) AND (androgens) AND (assisted reproduction) AND (cognitive decline) AND (compounds of similar chemical or biologic composition to hCG) AND (could interfere with the study protocol objectives) AND (follicle stimulating hormone) AND (hCG) AND (hormonal contraceptives) AND (insulin) AND (intercurrent illness) AND (medication) AND (prednisone) AND (previous) AND (receiving) AND (thyroid hormones) AND (treatment) AND (uncontrolled))"}
{"candidate_id": "LLM06534", "doc_id": "NCT00959569_inc", "case_bucket": "or", "source_criterion": "end diastolic diameter >60 mm and/or an ejection fraction <50% written informed consent age >18 years", "candidate_expression": "((age >18 years) AND (ejection fraction <50%) AND (end diastolic diameter >60 mm) AND (written informed consent))"}
{"candidate_id": "LLM06535", "doc_id": "NCT00812344_inc", "case_bucket": "other", "source_criterion": "body mass index (BMI) between 19 to 30 kg/m2 and body weight between 50 to 100 kg inclusive", "candidate_expression": "((body mass index (BMI) between 19 to 30 kg/m2) AND (body weight 50 to 100 kg inclusive))"}
{"candidate_id": "LLM06536", "doc_id": "NCT01717911_inc", "case_bucket": "other", "source_criterion": "Recently diagnosed type 2 diabetic patients. Fasting plasma glucose between 200-300 mg/dl (A1C level between 7% and 10%). Those who age between 30 and 80 years old and can inject insulin by themselves.", "candidate_expression": "((A1C level) AND (Fasting plasma glucose) AND (Recently diagnosed) AND (age) AND (between 200-300 mg/dl) AND (between 30 and 80 years old) AND (between 7% and 10%) AND (can) AND (inject insulin) AND (type 2 diabetic))"}
{"candidate_id": "LLM06537", "doc_id": "NCT03467750_exc", "case_bucket": "other", "source_criterion": "Known coagulation defect Patients on longstanding NSAID therapy Known renal impairment Patients may also be excluded at the discretion of the investigator", "candidate_expression": "((NSAID therapy longstanding) AND (coagulation defect) AND (renal impairment))"}
{"candidate_id": "LLM06538", "doc_id": "NCT03477851_exc", "case_bucket": "or", "source_criterion": "No consent Spinal anesthesia or sciatic nerve block contraindicated Known intolerance to tramadol or other contraindications for the drug", "candidate_expression": "((No) AND (No consent) AND (consent) AND (contraindicated) AND (contraindications) AND (intolerance) AND (other) AND (the drug) AND (tramadol) AND ((Spinal anesthesia) OR (sciatic nerve block)))"}
{"candidate_id": "LLM06539", "doc_id": "NCT02630628_exc", "case_bucket": "or", "source_criterion": "Renal disease unrelated to SLE (e.g. diabetes mellitus, other glomerular or tubulointerstitial disease, renovascular disease), or transplanted kidney. Estimated glomerular filtration rate (eGFR by MDRD) =20 mL/min per 1.73 m2 or serum creatinine >300 micromol/L (3.39 mg/dL) at screening. Renal biopsy showing cellular or fibrocellular crescent in more than 25% of glomeruli. CNS or other severe organ manifestation of lupus that necessitate aggressive immunosuppressive therapy on its own. Co-morbidities that require corticosteroid therapy (e.g. asthma, inflammatory bowel disease). Treatment with prednisolone (or prednisone, or equivalent) at >20 mg/D for over 4 weeks within the past 3 months. Treatment with MMF at >1.5 g/D for over 4 weeks within the past 3 months. Known hypersensitivity or intolerability to prednisolone (or prednisone, or equivalent), TAC, or MMF at a dose of 1.25 g or below per day. Subjects who are already on treatment with TAC, cyclosporine or any other calcineurin inhibitor for over 4 weeks within the past 12 months. Treatment with cyclophosphamide, leflunomide, or methotrexate for over 2 weeks, or use of biological agent(s) regardless of duration, within the past 6 months (Note: prior use of azathioprine, mizoribine, intravenous immunoglobulins and anti-malarials is allowed). Uncontrolled hypertension with systolic BP >160 mmHg or diastolic BP >95 mmHg. Women who are pregnant or breastfeeding. Women with childbearing potential or their male partners, who refuse to use an effective birth control method", "candidate_expression": "((1.25 g or below per day) AND (2 weeks) AND (3.39 mg/dL) AND (=20 mL/min per 1.73 m2) AND (>1.5 g/D for over 4 weeks) AND (>160 mmHg) AND (>20 mg/D for over 4 weeks) AND (>300 micromol/L) AND (>95 mmHg) AND (CNS) AND (Co-morbidities) AND (Estimated glomerular filtration rate) AND (MMF) AND (Renal biopsy) AND (Renal disease) AND (SLE) AND (TAC) AND (Uncontrolled) AND (Women who are pregnant or breastfeeding) AND (Women with childbearing potential or their male partners, who refuse to use an effective birth control method) AND (allowed) AND (anti-malarials) AND (asthma) AND (azathioprine) AND (biological agent) AND (calcineurin inhibitor) AND (cellular crescent) AND (corticosteroid therapy) AND (cyclophosphamide) AND (cyclosporine) AND (diabetes mellitus) AND (diastolic BP) AND (eGFR) AND (fibrocellular crescent) AND (glomerular disease) AND (hypersensitivity) AND (hypertension) AND (immunoglobulins) AND (immunosuppressive therapy) AND (inflammatory bowel disease) AND (intolerability) AND (leflunomide) AND (lupus) AND (methotrexate) AND (mizoribine) AND (more than 25% of glomeruli) AND (organ manifestation) AND (over 4 weeks) AND (past 12 months.) AND (past 3 months) AND (past 6 months) AND (prednisolone) AND (prednisone) AND (prednisone equivalent) AND (renovascular disease) AND (serum creatinine) AND (systolic BP) AND (transplanted kidney) AND (tubulointerstitial disease) AND (unrelated))"}
{"candidate_id": "LLM06540", "doc_id": "NCT03250507_inc", "case_bucket": "other", "source_criterion": "Elective open abdominal hysterectomy with midline incision, age > 18 years, American Society of Anesthesiologist classification score (ASA classification) 1-3.", "candidate_expression": "((1-3) AND (> 18 years) AND (ASA classification) AND (American Society of Anesthesiologist classification score) AND (Elective) AND (age) AND (midline incision) AND (open abdominal hysterectomy))"}
{"candidate_id": "LLM06541", "doc_id": "NCT03134196_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06542", "doc_id": "NCT02650024_exc", "case_bucket": "or", "source_criterion": "Amiodarone P-glycoprotein (P-gp) inducers (e.g., rifampin, St. John's wort) Liver biopsy at any time showing mHAI stage 4 or higher fibrosis OR FibroScan within 12 months demonstrating liver stiffness of =9.5 kilo Pascal or AST to platelet ratio index (APRI) =2.0 and Fibrosis-4 (FIB-4) =3.25 NOTE: If APRI and FIB-4 are discordant one of the other forms of fibrosis staging must be used. Known allergy/sensitivity or any hypersensitivity to components of study drugs or their formulation. Hemochromatosis Alpha-1 antitrypsin deficiency Wilson's disease Autoimmune hepatitis Alcoholic liver disease Drug-related liver disease Severe NC confounding conditions (stroke, head injury, or developmental learning disability). Regular use of anti-inflammatory drugs. Current or recent treatment with pegylated interferon (PEG-IFN). Other active inflammatory process (major infection, malignancy, rheumatoid arthritis/autoimmune disorder) within the prior 28 days. Contraindications to magnetic resonance imaging (MRI). Bleeding diathesis, thrombocytopenia, or use of anticoagulants that would contraindicate lumbar puncture. Uncontrolled or active depression or other psychiatric disorder that in the opinion of the site investigator might preclude adherence to study requirements or impact NC functioning and assessments. Active drug or alcohol use or dependence that, in the opinion of the site investigator, would interfere with adherence to study requirements. Presence of active or acute AIDS-defining opportunistic infections within 12 weeks prior to study entry.", "candidate_expression": "((4 or higher) AND (=2.0) AND (=3.25) AND (=9.5 kilo Pascal) AND (AIDS-defining opportunistic infections) AND (Active) AND (Alcoholic liver disease) AND (Alpha-1 antitrypsin deficiency) AND (Amiodarone) AND (Autoimmune hepatitis) AND (Contraindications) AND (Drug-related liver disease) AND (FibroScan) AND (Hemochromatosis) AND (Liver biopsy) AND (NC confounding conditions) AND (Other) AND (P-glycoprotein (P-gp) inducers) AND (PEG-IFN) AND (Wilson's disease) AND (active inflammatory process) AND (anti-inflammatory drugs) AND (any time) AND (components of study drugs) AND (contraindicate) AND (liver stiffness) AND (lumbar puncture) AND (mHAI stage) AND (magnetic resonance imaging (MRI)) AND (other) AND (pegylated interferon) AND (treatment) AND (within 12 months) AND (within 12 weeks prior to study entry) AND (within the prior 28 days) AND ((AST to platelet ratio index (APRI)) OR (Fibrosis-4 (FIB-4))) AND ((allergy) OR (hypersensitivity) OR (sensitivity)) AND ((developmental learning disability) OR (head injury) OR (stroke)) AND ((St. John's wort) OR (rifampin)) AND ((Current) OR (recent)) AND ((autoimmune disorder) OR (major infection) OR (malignancy) OR (rheumatoid arthritis)) AND ((Bleeding diathesis) OR (anticoagulants) OR (thrombocytopenia)) AND ((Uncontrolled) OR (active)) AND ((depression) OR (psychiatric disorder)) AND ((alcohol use or dependence) OR (drug use or dependence)) AND ((active) OR (acute)))"}
{"candidate_id": "LLM06543", "doc_id": "NCT00379366_inc", "case_bucket": "other", "source_criterion": "over 18 years successful angioplasty (residual stenosis < 30%) on a significant stenosis (maximal systolic speed 3 times > from basal maximal systolic speed, stenosis > 70% on angiography) on the venous-prosthesis anastomosis or on the venous segment 5 cm after the anastomosis of a prosthetic haemodialysis vascular access (at least 1 month old) social security affiliation signed informed consent", "candidate_expression": "((angiography) AND (maximal systolic speed 3 times > from basal) AND (on the venous segment 5 cm after the anastomosis angioplasty) AND (on the venous-prosthesis anastomosis angioplasty successful) AND (over 18 years over 18 years) AND (residual stenosis < 30%) AND (signed informed consent) AND (social security affiliation) AND (stenosis > 70%) AND (stenosis significant))"}
{"candidate_id": "LLM06544", "doc_id": "NCT02550028_inc", "case_bucket": "or", "source_criterion": "Male or female term baby with gestational >37 weeks and postnatal age < or= 28 days Birthweight >2500g Written informed consent of parent or guardian", "candidate_expression": "((< or= 28 days) AND (>2500g) AND (>37 weeks) AND (Birthweight) AND (Written informed consent of parent or guardian) AND (baby) AND (gestational) AND (postnatal age) AND (term) AND ((Male) OR (female)))"}
{"candidate_id": "LLM06545", "doc_id": "NCT02315287_inc", "case_bucket": "or", "source_criterion": "HbA1c > 13.0 % No treatment with insulin or oral agents for 6 months 20 = Age < 80 years", "candidate_expression": "((20 =) AND (< 80 years) AND (> 13.0 %) AND (Age) AND (HbA1c) AND (No) AND (for 6 months) AND (insulin) AND (oral agents) AND (treatment))"}
{"candidate_id": "LLM06546", "doc_id": "NCT02964715_exc", "case_bucket": "or", "source_criterion": "eGFR <45 ml/min structural and functional urogenital abnormalities, that predispose for urogenital infections Investigational product use in the last 6 months SGLT2 inhibitor, TZD, DPP4 inhibitor and GLP1 RA use within the past 6 months DKA(Diabetic Ketoacidosis) or HHS(Hyperosmoloar Hyperglycaemic Syndrome) within the last 6 months Pregnancy Presence of major contraindications to magnetic resonance imaging (cardiac pacemakers, claustrophobia, foreign bodies and implanted medical devices with ferromagnetic properties). Liver cirrhosis Type 1 diabetes Severe uncorrected insulin insufficiency Significant alcohol intake HIV infection Use of Traditional Chinese Medication or alternative therapies Coexisting causes of chronic liver disease - chronic viral hepatitis(B & C), autoimmune liver disease, hemochromatosis, Wilson's etc. Use of medications associated with steatosis eg. Methotrexate, anticonvulsants, antiretroviral therapy etc. h/o stroke Steroid therapy Endogenous Cushing's Familial hypertriglyceridemia", "candidate_expression": "((Cushing's Endogenous) AND (Diabetic Ketoacidosis) AND (Familial hypertriglyceridemi) AND (HIV infection) AND (Hyperosmoloar Hyperglycaemic Syndrome) AND (Investigational product use in the last 6 months) AND (Liver cirrhosis) AND (Pregnancy) AND (Steroid therapy) AND (Type 1 diabetes Severe uncorrected) AND (alcohol intake Significant) AND (cardiac pacemakers) AND (chronic liver disease) AND (claustrophobia) AND (eGFR <45 ml/min) AND (foreign bodies) AND (implanted medical devices ferromagnetic properties) AND (insulin insufficiency) AND (magnetic resonance imaging) AND (major contraindications) AND (medications) AND (predispose for urogenital infections) AND (steatosis) AND (stroke) AND (urogenital abnormalities) AND (urogenital infections) AND ((DPP4 inhibitor) OR (GLP1 RA) OR (SGLT2 inhibitor) OR (TZD)) AND ((DKA) OR (HHS)) AND ((Traditional Chinese Medication) OR (alternative therapies)) AND ((Wilson's) OR (autoimmune liver disease) OR (chronic viral hepatitis B) OR (chronic viral hepatitis C) OR (hemochromatosis)) AND ((functional) OR (structural)) AND ((Methotrexate) OR (anticonvulsants) OR (antiretroviral therapy)))"}
{"candidate_id": "LLM06547", "doc_id": "NCT02652637_inc", "case_bucket": "other", "source_criterion": "Patients undergoing colon resection", "candidate_expression": "((colon resection) AND (undergoing))"}
{"candidate_id": "LLM06548", "doc_id": "NCT03249272_exc", "case_bucket": "or", "source_criterion": "Decompensated heart failure or hemodynamic instability Prior coronary revascularization (PCI or CABG) or myocardial infarction (as evidenced by previously elevated CPK-MB or troponin levels) Accelerating angina or unstable angina Inability to physically tolerate MRI or implanted objects that are MRI incompatible Inability to provide written informed consent obtained at time of study enrollment. Severe claustrophobia Advanced heart block or sinus node dysfunction Hypersensitivity or allergic reaction to regadenoson or adenosine Hypotension Active bronchospasm or history of hospitalization due to bronchospasm History of seizures Recent cerebrovascular accident Use of dipyridamole within the last 5 days Contraindication to aminophylline Severe renal insufficiency with estimated glomerular filtration rate <30 ml/min/ 1.73 m2 Pregnant or nursing", "candidate_expression": "((<30 ml/min/ 1.73 m2) AND (Accelerating angina) AND (Active) AND (Advanced) AND (CABG) AND (CPK-MB levels) AND (Contraindication) AND (Decompensated) AND (History) AND (Hypersensitivity) AND (Hypotension) AND (Inability to physically tolerate) AND (Inability to provide written informed consent obtained at time of study enrollment.) AND (MRI) AND (MRI incompatible) AND (PCI) AND (Pregnant) AND (Prior) AND (Recent) AND (Severe) AND (adenosine) AND (allergic) AND (aminophylline) AND (bronchospasm) AND (cerebrovascular accident) AND (claustrophobia) AND (coronary revascularization) AND (dipyridamole) AND (elevated) AND (estimated glomerular filtration rate) AND (heart block) AND (heart failure) AND (hemodynamic instability) AND (history) AND (hospitalization) AND (implanted objects) AND (myocardial infarction) AND (nursing) AND (previously) AND (regadenoson) AND (renal insufficiency) AND (seizures) AND (sinus node dysfunction) AND (troponin levels) AND (unstable angina) AND (within the last 5 days))"}
{"candidate_id": "LLM06549", "doc_id": "NCT02443623_exc", "case_bucket": "or", "source_criterion": "History of severe related adverse event(s) from previous participation in VA-001 or VA-006 trials or to any smallpox vaccination. Eczema, history of eczema, exfoliative skin conditions, wounds, burns, or other skin conditions at the investigator's discretion. A history of immunodeficiency. Currently or has recently received radiotherapy or chemotherapy, adrenocorticotropic hormone (ACTH), corticosteroids, or immunosuppressive drugs. Eye disease treated with topical steroids. Known or suspected disorders of immunoglobulin synthesis. Leukemia, lymphomas of any type, melanoma, or other malignant neoplasms affecting the bone marrow or lymphatic systems. Has been diagnosed with cancer and who will be undergoing chemotherapy or radiation therapy during the vaccination healing time. Is a transplant recipient (except for corneal transplant). Is pregnant, planning pregnancy or breast feeding (female subjects of childbearing potential must have negative pregnancy test prior to vaccination). Household or other close/intimate contact(s) under the age of 12 months. History of allergies to phenol, any of the antibiotics listed in the vaccine content, or any other component of ACAM2000 or its diluents. Subjects with kidney disease (except kidney stones). Subjects with abnormal EKG at screening (if applicable). To mitigate the risk of enrolling at risk subjects and potentially jeopardizing subject safety an EKG will be performed prior to vaccination with ACAM2000 smallpox vaccine in all potential subjects =50 years old and for all potential subjects <50 with two cardiac risk factors as listed immediately below including; severely or morbidly obese or higher obesity classification (BMI =36); high blood pressure; high blood cholesterol; diabetes or high blood sugar; a first degree relative who had a heart condition before the age of 50; and current tobacco smokers. Severely or morbidly obese or higher obesity classification (BMI =36) High blood pressure diagnosed by a doctor High blood cholesterol diagnosed by a doctor Diabetes or high blood sugar diagnosed by a doctor A first degree relative (for example, mother, father, brother, sister) who had a heart condition before the age of 50 Currently smokes tobacco (cigarettes) Arrhythmia Syncope related to cardiac disease Previous myocardial infarction Angina Coronary artery disease Congestive heart failure Cardiomyopathy Stroke or transient ischemic attack Myocarditis Pericarditis Chest pain or shortness of breath with activity (such as climbing stairs), peripheral edema, heart palpitations, dry cough, irregular heartbeat, excessive fatigue, unexplained syncope Other heart conditions being treated by a physician", "candidate_expression": "((50) AND (=36) AND (A first degree relative) AND (ACTH) AND (Angina) AND (Arrhythmia) AND (Cardiomyopathy) AND (Congestive heart failure) AND (Coronary artery disease) AND (EKG) AND (Eye disease) AND (High blood cholesterol) AND (High blood pressure) AND (Myocarditis) AND (Other heart conditions) AND (Pericarditis) AND (Previous myocardial infarction) AND (Severely) AND (Syncope) AND (abnormal) AND (adverse event) AND (age) AND (age of 50) AND (allergies) AND (at screening) AND (at the investigator's discretion) AND (before the age of 50) AND (bone marrow) AND (cardiac disease) AND (childbearing potential) AND (corneal transplant) AND (diagnosed with cancer) AND (disorders of immunoglobulin synthesis) AND (during the vaccination healing time) AND (except) AND (female) AND (heart condition) AND (history of immunodeficiency) AND (kidney disease) AND (kidney stones) AND (listed in the vaccine content) AND (lymphatic systems) AND (morbidly) AND (negative) AND (pregnancy test) AND (prior to vaccination) AND (recently) AND (screening) AND (smallpox vaccination) AND (smokes cigarettes) AND (smokes tobacco) AND (topical steroids) AND (transplant recipient) AND (under 12 months) AND (vaccination) AND (vaccination healing time) AND (vaccine) AND ((Stroke) OR (transient ischemic attack)) AND ((Chest pain) OR (dry cough) OR (excessive fatigue) OR (heart palpitations) OR (irregular heartbeat) OR (peripheral edema) OR (shortness of breath with activity) OR (syncope)) AND ((adrenocorticotropic hormone) OR (chemotherapy) OR (corticosteroids) OR (immunosuppressive drugs) OR (radiotherapy)) AND ((Known) OR (suspected)) AND ((Leukemia) OR (lymphomas) OR (malignant neoplasms) OR (melanoma)) AND ((affecting lymphatic systems) OR (affecting the bone marrow)) AND ((chemotherapy) OR (radiation therapy)) AND ((Eczema) OR (burns) OR (exfoliative skin conditions) OR (history of eczema) OR (other skin conditions) OR (wounds)) AND ((breast feeding) OR (planning pregnancy) OR (pregnant)) AND ((Household) OR (close/intimate contact(s))) AND ((ACAM2000) OR (ACAM2000 diluents) OR (antibiotics) OR (phenol)) AND ((BMI) OR (higher obesity classification) OR (obese)) AND ((Diabetes) OR (high blood sugar)) AND ((brother) OR (father) OR (mother) OR (sister)))"}
{"candidate_id": "LLM06550", "doc_id": "NCT02667730_exc", "case_bucket": "or", "source_criterion": "Diagnosis of ankle fracture or ligament rupture Has planned release from the Canadian Armed Forces within one year; Documented restrictions on military duties Has known intolerance or documented adverse reaction to acetaminophen or naproxen or celecoxib Documented history of liver or kidney problems pregnant or breastfeeding", "candidate_expression": "((history) AND (release from the Canadian Armed Forces) AND (restrictions on military duties) AND (within one year) AND ((ankle fracture) OR (ligament rupture)) AND ((kidney problems) OR (liver problems)) AND ((breastfeeding) OR (pregnant)) AND ((acetaminophen) OR (celecoxib) OR (naproxen)) AND ((adverse reaction) OR (intolerance)))"}
```
