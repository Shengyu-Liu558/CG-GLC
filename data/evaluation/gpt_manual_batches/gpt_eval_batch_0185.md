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
{"candidate_id": "LLM04601", "doc_id": "NCT02429583_exc", "case_bucket": "or", "source_criterion": "Received any vaccine within a month prior to study vaccine Positive serum antibody against Hep B surface antigen and/or core Hep B core antigen HIV positive For HCV-negative, healthy volunteers: History of HCV infection or positive HCV antibody test Participation in another clinical study of an investigational product currently or within the past 90 days, or expected participation during this study In the opinion of the investigator, the volunteer is unlikely to comply with the study protocol Any clinically significant abnormality or medical history or physical examination including history of immunodeficiency or autoimmune disease (in addition to HCV infection, for HCV group) Currently taking systemic steroids or other immunomodulatory medications including anticancer medications and antiviral medications Any clinically significant acute or chronic medical condition requiring care by a primary care provider (e.g., diabetes, coronary artery disease, rheumatologic illness, malignancy, substance abuse) that, in the opinion of the investigator, would preclude participation Unable to continue participation for 156 weeks History of previous Hepatitis B vaccination(s) Male or female < 18 and > 62 years of age Is pregnant or lactating History of Hepatitis B infection Clinical, laboratory, or biopsy evidence of cirrhosis", "candidate_expression": "((< 18 and > 62 years) AND (HCV) AND (HCV infection) AND (HIV) AND (Hepatitis B infection) AND (Hepatitis B vaccination) AND (History of HCV infection) AND (In the opinion of the investigator, the volunteer is unlikely to comply with the study protocol) AND (Is pregnant or lactating) AND (Participation in another clinical study of an investigational product currently or within the past 90 days, or expected participation during this study) AND (Positive) AND (Unable to continue participation for 156 weeks) AND (age) AND (cirrhosis) AND (in addition to) AND (negative) AND (positive) AND (serum antibody) AND (study vaccine) AND (vaccine) AND (within a month prior to study vaccine) AND ((autoimmune disease) OR (immunodeficiency)) AND ((immunomodulatory medications) OR (systemic steroids)) AND ((anticancer medications) OR (antiviral medications)) AND ((coronary artery disease) OR (diabetes) OR (malignancy) OR (rheumatologic illness) OR (substance abuse)) AND ((Male) OR (female)) AND ((Hep B surface antige) OR (core Hep B core antigen)))"}
{"candidate_id": "LLM04602", "doc_id": "NCT02984475_inc", "case_bucket": "scope", "source_criterion": "Diagnosed with Beta-Thalassemia Major and receiving regular blood transfusion and on iron chelating therapy. Weight: equal to or over 35 kg. Normal renal function.", "candidate_expression": "((Beta-Thalassemia Major) AND (Weight equal to or over 35 kg) AND (blood transfusion) AND (iron chelating therapy) AND (renal function Normal))"}
{"candidate_id": "LLM04603", "doc_id": "NCT02527512_inc", "case_bucket": "other", "source_criterion": "Age 3 to 18 years on day of surgery diagnosis of spinal deformity undergoing elective posterior spine multi-level instrumentation surgery", "candidate_expression": "((Age 3 to 18 years on day of surgery) AND (multi-level instrumentation surgery undergoing elective posterior spine) AND (spinal deformity))"}
{"candidate_id": "LLM04604", "doc_id": "NCT03073603_inc", "case_bucket": "or", "source_criterion": "Patients with either Relapsing-remitting MS (RRMS), Secondary progressive MS (SPMS), or Primary progressive MS (PPMS) by McDonald 2010 criteria. Patients defined by subtype based on 2013 updated phenotypic criteria. prospectively with an EDSS change of at least 1.0 points over the last two years, or retrospectively, with any significant change in motor function over at least one year, unrelated to relapse. 55 years of age or older at time of randomization; No evidence of recent new inflammatory disease activity (inactive by the Lublin criteria16) with no new relapse for at least five years and no new MRI lesion for at least three years interferon ß-1a, interferon ß-1b, glatiramer acetate, natalizumab, fingolimod, dimethyl fumarate, or teriflunomide; continuously for no less than 5 years. Taking most recent DMT continuously* for no less than two years. Willing to be randomized per this protocol; each patient will be questioned as to their willingness to stay in the trial regardless of the group to which group they are randomized. Willing to follow the protocol Continuously will be defined as no less than 75% of all prescribed doses, with no time of greater than four weeks from last intended dose to have missed a dose (8 weeks for natalizumab, i.e. one missed dose).", "candidate_expression": "((DMT continuously for no less than two years) AND (EDSS change at least 1.0 points over the last two years) AND (Lublin criteria inactive) AND (MRI) AND (Willing to be randomized per this protocol; each patient will be questioned as to their willingness to stay in the trial regardless of the group to which group they are randomized.) AND (Willing to follow the protocol) AND (age 55 years or older at time of randomization) AND (change in motor function significant over at least one year unrelated to relapse) AND (dimethyl fumarate) AND (fingolimod) AND (glatiramer acetate) AND (interferon ß-1a) AND (interferon ß-1b) AND (natalizumab) AND (teriflunomide continuously for no less than 5 years) AND NOT (inflammatory disease new) AND NOT (relapse new for at least five years) AND NOT (lesion new for at least three years) AND ((Primary progressive MS (PPMS)) OR (Relapsing-remitting MS (RRMS)) OR (Secondary progressive MS (SPMS))))"}
{"candidate_id": "LLM04605", "doc_id": "NCT03390933_inc", "case_bucket": "other", "source_criterion": "currently on hemodialysis at a CDC dialysis unit English speaking able to provide informed consent", "candidate_expression": "((CDC dialysis unit) AND (English speaking) AND (able to provide informed consent) AND (currently) AND (hemodialysis))"}
{"candidate_id": "LLM04606", "doc_id": "NCT02952963_exc", "case_bucket": "or", "source_criterion": "Fasting plasma glucose > 7,0 mM, HbA1c > 48 mmol/mol 3 months after RYGB Dysregulated thyroid diseases, use of antithyroid treatment. Late diabetic complications as retinopathy, renal insufficiency, neuropathy or previous pancreatitis. Complications to RYGB. Documented reactive hypoglycaemia, severe dumping (vomiting, diarrhea, severe abdominal pain after food intake) Cholecystectomy.", "candidate_expression": "((Cholecystectomy) AND (Complications) AND (Fasting plasma glucose > 7,0 mM) AND (HbA1c > 48 mmol/mol) AND (Late diabetic complications) AND (RYGB) AND (abdominal pain severe after food intake) AND (antithyroid treatment) AND (diarrhea) AND (dumping severe) AND (neuropathy) AND (pancreatitis previous) AND (reactive hypoglycaemia) AND (renal insufficiency) AND (retinopathy) AND (thyroid diseases Dysregulated) AND (vomiting))"}
{"candidate_id": "LLM04607", "doc_id": "NCT03493919_inc", "case_bucket": "or", "source_criterion": "Subjects who, in the opinion of the investigator, can and will comply with the requirements of the protocol. Written informed consent obtained from the subject prior to performing any study specific procedure. A male or female between, and including, 18 and 50 years of age at the time of the first study visit. Healthy subjects as established by medical history and clinical examination before entering into the study. Healthy subjects with no medical conditions that, in the opinion of the investigator, prevents the subject from participating in the study. Subjects must weigh at least 110 pounds (50 kg), but not to present obesity (BMI < 32kg/m2). Female subjects of non-childbearing potential may be enrolled in the study. Non-childbearing potential is defined as pre-menarche, current bilateral tubal ligation or occlusion, hysterectomy, bilateral ovariectomy or post-menopause. has practiced adequate contraception for 30 days prior to vaccination, and has a negative pregnancy test on the day of vaccination and has agreed to continue adequate contraception during the entire treatment period and for 1 month, after completion of the vaccination series.", "candidate_expression": "((BMI < 32kg/m2) AND (Female) AND (Healthy medical history before entering into the study) AND (Written informed consent prior to performing any study specific procedure) AND (adequate contraception continue) AND (age 18 and 50 years at the time of the first study visit) AND (bilateral ovariectomy) AND (bilateral tubal ligation) AND (bilateral tubal occlusion) AND (clinical examination) AND (comply with the requirements of the protocol) AND (contraception adequate 30 days prior to vaccination) AND (pregnancy test negative on the day of vaccination) AND (study specific procedure) AND (weigh at least 110 pounds at least 50 kg) AND NOT (obesity) AND NOT (childbearing potential) AND ((bilateral tubal ligation) OR (bilateral tubal occlusion)) AND ((bilateral ovariectomy) OR (hysterectomy) OR (post-menopause) OR (pre-menarche)) AND ((during the entire treatment period) OR (for 1 month, after completion of the vaccination series completion of the vaccination series)) AND ((female) OR (male)))"}
{"candidate_id": "LLM04608", "doc_id": "NCT03008005_exc", "case_bucket": "or", "source_criterion": "clinically significant medical or neurologic condition or neurocognitive dysfunction that would affect function and/or task performance and/or interfere with the study protocol any current (or within past 2 months) medical condition requiring medication that would interact with dronabinol or interfere with the study protocol risk of harm to self or others that requires immediate intervention presence of contraindications, current or past allergic or adverse reaction, or known sensitivity to cannabinoid-like substances (dronabinol/marijuana/cannabis/THC, cannabinoid oil, sesame oil, gelatin, glycerin, and titanium dioxide) lack of fluency in English positive drug screen or alcohol breathalyzer unwilling/unable to sign informed consent document currently pregnant (positive pregnancy test), planning pregnancy, or lactating (women) under 18 or over 50 years of age traumatic brain injury (as defined by The American Congress of Rehabilitation as a person who has had a traumatically induced physiological disruption of brain function (i.e., the head being struck, the head striking an object, and/or the brain undergoing an acceleration/deceleration movement (i.e., whiplash) without direct external trauma to the head), as manifested by at least one of the following: any loss of consciousness; any loss of memory for events immediately before or after the injury; any alteration in mental status at the time of the incident; or focal neurological deficits that may or may not be transient) inability to tolerate small, enclosed spaces without anxiety (e.g. claustrophobia), as determined by self-report and/or a preliminary session in a mock scanner left-handed; presence of ferrous-containing metals within the body (e.g., aneurysm clips, shrapnel/retained particles) anticipation of a required drug test in the 4 weeks following the study. current diagnosis of a mood, anxiety, or other disorder that is more clinically salient than PTSD current moderate or severe alcohol/drug use disorder or in the past 8 weeks current or past diagnosis of bipolar and other related disorders, schizophrenia spectrum, or other psychotic disorders concomitant treatments with medication known to have drug interactions with dronabinol, such as, central nervous system depressants (barbiturates, benzodiazepines, buspirone, lithium, etc) and anticholinergic agents (atropine, scopolamine, antihistamines, etc).", "candidate_expression": "((PTSD) AND (THC) AND (adverse reaction) AND (age) AND (alcohol breathalyzer) AND (alcohol use disorder) AND (allergic reaction) AND (aneurysm clips) AND (anticholinergic agents) AND (anticipation of) AND (antihistamines) AND (anxiety disorder) AND (atropine) AND (barbiturates) AND (benzodiazepines) AND (bipolar) AND (buspirone) AND (cannabinoid oil) AND (cannabinoid-like substances) AND (cannabis) AND (central nervous system depressants) AND (claustrophobia) AND (clinically significant) AND (contraindications) AND (current) AND (currently) AND (disorder) AND (dronabinol) AND (drug interactions) AND (drug screen) AND (drug test) AND (drug use disorder) AND (ferrous-containing metals) AND (gelatin) AND (glycerin) AND (in the 4 weeks following the study) AND (in the past 8 weeks) AND (inability) AND (interfere with the study protocol) AND (lactating) AND (left-handed) AND (lithium) AND (marijuana) AND (medical condition) AND (medication) AND (moderate) AND (mood disorder) AND (more clinically salient than PTSD) AND (neurocognitive dysfunction) AND (neurologic condition) AND (other) AND (past) AND (planning) AND (positive) AND (pregnancy) AND (pregnancy test) AND (pregnant) AND (psychotic disorders) AND (related disorders) AND (retained particles) AND (schizophrenia spectrum) AND (scopolamine) AND (self-report) AND (sensitivity) AND (sesame oil) AND (severe) AND (shrapnel) AND (titanium dioxide) AND (tolerate small, enclosed spaces without anxiety) AND (traumatic brain injury) AND (treatments) AND (under 18 or over 50 years) AND (unwilling/unable to sign informed consent document) AND (within past 2 months) AND (would interact with))"}
{"candidate_id": "LLM04609", "doc_id": "NCT02150590_exc", "case_bucket": "or", "source_criterion": "unstable condition, COPD exacerbation mild (GOLD 1) or very severe COPD (GOLD 4) requirement for oxygen therapy at low altitude residence hypoventilation pulmonary hypertension more than mild or unstable cardiovascular disease use of drugs that affect respiratory center drive internal, neurologic or psychiatric disease that interfere with protocol compliance including current heavy smoking (>20 cigarettes per day), inability to perform 6 min walk test. previous intolerance to moderate altitude (<2600m). exposure to altitudes >1500m for >2 days within the last 4 weeks before the study. pregnant or nursing patients", "candidate_expression": "((GOLD 1)) AND (GOLD 4) AND (cardiovascular disease) AND (hypoventilation) AND (intolerance altitude) AND (oxygen therapy) AND (pregnant or nursing patients) AND (pulmonary hypertension) AND (smoking heavy >20 cigarettes per day) AND NOT (6 min walk test) AND ((COPD mild) OR (COPD very severe)) AND ((more than mild) OR (unstable)) AND ((internal disease) OR (neurologic disease) OR (psychiatric disease)) AND ((COPD exacerbation) OR (condition unstable)))"}
{"candidate_id": "LLM04610", "doc_id": "NCT02905890_exc", "case_bucket": "or", "source_criterion": "Currently pregnant or using a reliable contraception (e.g. injectables, intrauterine devices, implant, oral contraceptive pills) Desiring pregnancy in the next year History of tubal ligation or hysterectomy Contraindication to progestin-only contraceptives Unable to comprehend consent material because of language barrier or psychological difficulty", "candidate_expression": "((Currently pregnant or using a reliable contraception (e.g. injectables, intrauterine devices, implant, oral contraceptive pills)) AND (Desiring pregnancy in the next year) AND (Unable to comprehend consent material because of language barrier or psychological difficulty) AND (contraceptives) AND (progestin only) AND ((hysterectomy) OR (tubal ligation)))"}
{"candidate_id": "LLM04611", "doc_id": "NCT03663387_exc", "case_bucket": "or", "source_criterion": "Uncontrolled hypertension or metabolic disease Neurodegenerative disorders (i.e. Parkinson disease. LBD, or FTD). Dementia or Mild cognitive impairment at baseline Long life major depression. Baseline scores =16 on the 17-item Hamilton Depression Scale at baseline. Long-life DSM-IV axis 1 disorders. Mental retardation. Substance abuse. Concurrent medication limiting validity of neuropsychological tests or imaging. Anti-depressants with anti-cholinergic properties Monoamine oxidase inhibitors (MAOi) Regular use of narcotic analgesics (>2 doses per week). Use of neuroleptics Use of anti-dementia medications (Aricept, Exelon, Razadyne) and memantine (Namenda)) or anti-Parkinsonian medications (Sinemet, amantadine, bromocriptine, pergolide, selegeline). Individuals taking over the counter memory enhancing or protecting medications (e.g. ginkgo biloba, vitamins) are not excluded. Implanted medical devices that are incompatible with MRI imaging. Radiation exposures exceeding annual Rad Worker limits. Heart failure stage D as defined by American Heart Association (7). Chronic kidney disease in stages = 4, as defined per National Kidney Foundation (8). Brain tumor and other neoplastic disorders outside the brain where disease itself or its treatment (radiation, chemotherapy) is likely to affect brain structure or function. Stroke when meeting criteria for total anterior, partial anterior or posterior circulation infarct according to the Oxford Community Stroke Project classification. Patients with clinically silent of lacunar strokes and transient ischemic attacks will not be excluded. Significant head trauma. Hydrocephalus. Hostility or refusal to cooperate", "candidate_expression": "((17-item Hamilton Depression Scale) AND (= 4) AND (=16) AND (>2 doses per week) AND (American Heart Association) AND (Anti-depressants) AND (Baseline scores) AND (Chronic kidney disease) AND (Concurrent) AND (D) AND (Heart failure) AND (Hydrocephalus) AND (Long life major depression) AND (Long-life DSM-IV axis 1 disorders) AND (MRI imaging) AND (Mental retardation) AND (Mild) AND (Monoamine oxidase inhibitors (MAOi)) AND (Namenda) AND (National Kidney Foundation) AND (Neurodegenerative disorders) AND (Oxford Community Stroke Project classification) AND (Radiation exposures) AND (Regular use) AND (Significant) AND (Stroke) AND (Substance abuse) AND (Uncontrolled) AND (anti-cholinergic) AND (anti-cholinergic properties) AND (at baseline) AND (baseline) AND (circulation infarct) AND (cognitive impairment) AND (exceeding annual Rad Worker limits) AND (head trauma) AND (incompatible with MRI imaging) AND (medical devices) AND (medication) AND (narcotic analgesics) AND (neuroleptics) AND (outside the brain) AND (over the counter memory enhancing medications) AND (over the counter memory protecting medications) AND (stage) AND (stages) AND ((hypertension) OR (metabolic disease)) AND ((Dementia) OR (Mild cognitive impairment)) AND ((limiting validity of imaging) OR (limiting validity of neuropsychological tests)) AND ((Aricept) OR (Exelon) OR (Razadyne)) AND ((anti-Parkinsonian medications) OR (anti-dementia medications) OR (memantine)) AND ((Sinemet) OR (amantadine) OR (bromocriptine) OR (pergolide) OR (selegeline)) AND ((ginkgo biloba) OR (vitamins)) AND ((Brain tumor) OR (chemotherapy) OR (neoplastic disorders) OR (radiation)) AND ((likely to affect brain function) OR (likely to affect brain structure)) AND ((FTD) OR (LBD) OR (Parkinson disease)) AND ((partial anterior) OR (posterior) OR (total anterior)) AND ((Hostility) OR (refusal to cooperate)))"}
{"candidate_id": "LLM04612", "doc_id": "NCT03250507_inc", "case_bucket": "other", "source_criterion": "Elective open abdominal hysterectomy with midline incision, age > 18 years, American Society of Anesthesiologist classification score (ASA classification) 1-3.", "candidate_expression": "((ASA classification) AND (American Society of Anesthesiologist classification score 1-3) AND (age > 18 years) AND (open abdominal hysterectomy Elective midline incision))"}
{"candidate_id": "LLM04613", "doc_id": "NCT00351611_exc", "case_bucket": "or", "source_criterion": "Pre-existing eye diseases (glaucoma). Insufficient response to pregabalin in the treatment of partial seizure, or patients currently receiving pregabalin treatment.", "candidate_expression": "((Pre-existing) AND (eye diseases) AND (glaucoma) AND (partial seizure) AND (pregabalin) AND ((Insufficient response) OR (pregabalin)))"}
{"candidate_id": "LLM04614", "doc_id": "NCT02632318_exc", "case_bucket": "other", "source_criterion": "Regular cigarette smoker Alcohol abuse Drug abuse", "candidate_expression": "((Alcohol abuse) AND (Drug abuse) AND (Regular cigarette smoker))"}
{"candidate_id": "LLM04615", "doc_id": "NCT03624517_exc", "case_bucket": "or", "source_criterion": "Known upper gastrointestinal malignancy Bleeding from gastric varices, with or without esophageal varices Use of any other endoscopic method to stop GI bleeding beyond endoscopic band ligation Variceal bleeding in the last 90 days History of transjugular, intrahepatic, portosystemic shunt (TIPS) or vascular decompression surgery Pregnant females Incarcerated individuals Myocardial infarct, cerebrovascular accident, sepsis, respiratory failure, or severe intercurrent illness within the previous 6 weeks Non-cirrhotic portal hypertension causing esophageal varices Known or suspected allergy to octreotide", "candidate_expression": "((Bleeding) AND (GI bleeding) AND (History) AND (Incarcerated individuals) AND (Non-cirrhotic portal hypertension) AND (Pregnant) AND (Variceal bleeding) AND (allergy) AND (any other) AND (endoscopic band ligation) AND (endoscopic method) AND (esophageal varices) AND (females) AND (gastric varices) AND (in the last 90 days) AND (octreotide) AND (severe) AND (upper gastrointestinal malignancy) AND (within the previous 6 weeks) AND ((transjugular, intrahepatic, portosystemic shunt (TIPS)) OR (vascular decompression surgery)) AND ((Myocardial infarct) OR (cerebrovascular accident) OR (intercurrent illness) OR (respiratory failure) OR (sepsis)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM04616", "doc_id": "NCT03340740_exc", "case_bucket": "other", "source_criterion": "Use of antihistamine within the past 72 hours Chronic Pulmonary Condition other than asthma Other contraindication to cetirizine Severe asthma exacerbation requiring resuscitation", "candidate_expression": "((Chronic Pulmonary Condition) AND (antihistamine within the past 72 hours) AND (asthma exacerbation Severe) AND (cetirizine) AND (contraindication) AND (resuscitation) AND NOT (asthma))"}
{"candidate_id": "LLM04617", "doc_id": "NCT02765035_exc", "case_bucket": "or", "source_criterion": "Person is under 18 years of age. Person who weighs more than 136kg. Person who weighs less than 50kg. Person who is pregnant. Person has a history of chronic skin breakdown on the residual limb. Person has conditions that would prevent participation and pose increased risk (e.g. unstable cardiovascular conditions that preclude physical activity such as walking). Person falls = once a week due to the reasons that could not be corrected by the new prosthesis (for ex. problems with vestibular system). Person is using under arm axillary crutches or walker. Person in an emergency, life threatening situation. Person is unwilling/unable to follow instructions. Person who is not available to follow the entire study protocol. Person who is participating in another study or intends to participate in another study during this study duration. Person who cannot personally provide their consent. Person who is not wearing prosthesis 8hours/day on average. Person who has a score on 10m walk test less than 3km/h (~0.8m/s) (based on 10m walk test conducted during recruiting). Person who walks on average less than 1km per day. Person who is not able to walk on level ground in a step over step manner.", "candidate_expression": "((10m walk test less than 3km/h 0.8m/s)) AND (Person is unwilling/unable to follow instruction) AND (Person who cannot personally provide their consent) AND (Person who is not available to follow the entire study protocol) AND (Person who is participating in another study or intends to participate in another study during this study duration.) AND (age under 18 years) AND (emergency situation) AND (falls once a week) AND (life threatening situation) AND (pregnant) AND (skin breakdown chronic residual limb) AND (under arm axillary crutches) AND (walker) AND (walks ess than 1km per day) AND (weighs less than 50kg) AND (weighs more than 136kg) AND NOT (prosthesis 8hours/day))"}
{"candidate_id": "LLM04618", "doc_id": "NCT02867618_exc", "case_bucket": "or", "source_criterion": "1. Prior Therapy Exposure to chemotherapy or radiotherapy within 2 weeks prior to entering the study or those who have not recovered from adverse events due to agents administered more than 2 weeks earlier. Systemic steroids that have not been stabilized (≥ 5 days) to the equivalent of ≤10 mg/day prednisone prior to the start of the study drugs. No other investigational agents are allowed. 2. History of allergic reactions to TGR-1202 or carfilzomib 3. Uncontrolled inter-current illness 4. Pregnant women 5. Nursing women 6. Current malignancy or history of a prior malignancy 7. Patient known to be Human Immunodeficiency Virus (HIV)-positive 8. Active Hepatitis A, Hepatitis B, or Hepatitis C infection", "candidate_expression": "((Current) AND (History) AND (Human Immunodeficiency Virus (HIV)) AND (Nursing) AND (Pregnant) AND (Prior) AND (Systemic steroids) AND (Uncontrolled) AND (adverse events) AND (agents) AND (allergic reactions) AND (due to) AND (entering the study) AND (history of a prior) AND (inter-current) AND (inter-current illness) AND (more than 2 weeks earlier) AND (not) AND (other investigational agents) AND (positive) AND (prednisone) AND (prior to) AND (recovered) AND (stabilized) AND (start of the study drugs) AND (within 2 weeks prior) AND (women) AND (≤10 mg/day) AND (≥ 5 days) AND ((chemotherapy) OR (radiotherapy)) AND ((TGR-1202) OR (carfilzomib)) AND ((malignancy)) AND ((Hepatitis A) OR (Hepatitis B) OR (Hepatitis C)))"}
{"candidate_id": "LLM04619", "doc_id": "NCT03058835_inc", "case_bucket": "or", "source_criterion": "18 - 64 years old Able to give consent unprotected sex (in past 6 months) with 1 or more men of unknown HIV status evaluated for an STI within 6 months prior to screening sex in last 6 months with an HIV-infected partner IDU with report of using previously used or shared needles in past 6 months or has been in a methadone, buprenorphine, or suboxone treatment program in past 6 months or engaging in high-risk sexual behaviors individuals engaging in transactional sex (i.e sex for money, drugs, or housing) Infrequently uses condoms during sex with 1 or more partners of unknown HIV status who are known to be at substantial risk of HIV infection (IDU or bisexual male partner) CrCl = 60 ml/min HIV- uninfected women desiring PrEP", "candidate_expression": "((CrCl = 60 ml/min) AND (HIV- uninfected) AND (HIV-infected partner) AND (IDU) AND (Infrequently uses condoms during sex) AND (PrEP desiring) AND (bisexual male partner) AND (buprenorphine) AND (engaging in high-risk sexual behaviors) AND (evaluated for an STI within 6 months prior to screening) AND (men of unknown HIV status 1 or more) AND (methadone) AND (old 18 - 64 years) AND (partners of unknown HIV status 1 or more at substantial risk of HIV infection) AND (sex for drugs) AND (sex for housing) AND (sex for money) AND (sex in last 6 months) AND (suboxone) AND (transactional sex) AND (treatment program in past 6 months) AND (unprotected sex in past 6 months) AND (using previously used or shared needles in past 6 months) AND (women))"}
{"candidate_id": "LLM04620", "doc_id": "NCT02726009_inc", "case_bucket": "other", "source_criterion": "Has given written informed consent before any study-related activity is performed Advanced hormone-dependent prostate cancer for which androgen deprivation therapy is indicated, and independently from this trial, Firmagon® is intended to be used for treatment Age greater than or equal to 18 years and less than 80 years Advanced hormone-dependent prostate cancer without any other clinically significant disorder Easten Cooperative Oncology Group score = 2 PSA = 2 ng/mL at screening Life expectancy of at least 12 months as per the investigator's judgement", "candidate_expression": "((= 2) AND (= 2 ng/mL) AND (Advanced) AND (Age) AND (Easten Cooperative Oncology Group score) AND (Firmagon) AND (Has given written informed consent before any study-related activity is performed) AND (Life expectancy) AND (PSA) AND (androgen deprivation therapy) AND (at least 12 months) AND (greater than or equal to 18 years and less than 80 years) AND (hormone-dependent) AND (intended) AND (prostate cancer))"}
{"candidate_id": "LLM04621", "doc_id": "NCT01639664_inc", "case_bucket": "other", "source_criterion": "All patients admitted to the ICU in septic shock All patients that develop septic shock while in the ICU", "candidate_expression": "((ICU) AND (admitted) AND (septic shock) AND (septic shock while in the ICU))"}
{"candidate_id": "LLM04622", "doc_id": "NCT01630954_exc", "case_bucket": "or", "source_criterion": "Partial mole History of treatment for molar pregnancy like prior evacuation or chemotherapy Women requiring hysterectomy for treatment of H Mole", "candidate_expression": "((H Mole) AND (Partial mole) AND (Women) AND (hysterectomy) AND (molar pregnancy) AND (treatment) AND ((chemotherapy) OR (evacuation)))"}
{"candidate_id": "LLM04623", "doc_id": "NCT02714725_inc", "case_bucket": "or", "source_criterion": "Adult patients aged (>18), males and females, undergoing elective coronary artery bypass graft (CABG) surgery with cardiopulmonary bypass (CPB).", "candidate_expression": "((>18) AND (CABG) AND (CPB) AND (aged) AND (cardiopulmonary bypass) AND (elective) AND (surgery coronary artery bypass graft) AND ((females) OR (males)))"}
{"candidate_id": "LLM04624", "doc_id": "NCT02984228_exc", "case_bucket": "or", "source_criterion": "Non-English speaking/illiterate Painful active, concurrent cervical spine conditions Current non-steroidal anti-inflammatory drug (NSAID) use History of taking coumadin or similar anticoagulant, have a known coagulopathy, bleeding dyscrasia, or platelet count < 150,000/cubic mm Allergic reaction to poultry or previous viscosupplementation Involved in workers' compensation or active litigation involving affected shoulder Inability to refrain from NSAID use for 5 days prior to and 6 weeks after injection History of corticosteroid injection to affected shoulder within the last 3 months History of viscosupplementation or platelet-rich plasma to affected shoulder within the last 6 months Presence of acute fracture History of shoulder tumor Known uncontrolled systemic illness (uncontrolled diabetes, human immunodeficiency virus, vasculitis, autoimmune/inflammatory disease) Psychiatric and somatoform disorders", "candidate_expression": "((5 days prior to and 6 weeks after injection) AND (< 150,000/cubic mm) AND (Allergic reaction) AND (History of) AND (Inability to refrain from) AND (NSAID) AND (Non-English speaking/illiterate) AND (Painful) AND (acute) AND (cervical spine conditions) AND (corticosteroid injection) AND (fracture) AND (injection) AND (last 3 months) AND (last 6 months) AND (non-steroidal anti-inflammatory drug) AND (shoulder) AND (shoulder tumor) AND (systemic illness) AND (uncontrolled) AND ((poultry) OR (viscosupplementation)) AND ((platelet-rich plasma) OR (viscosupplementation)) AND ((autoimmune) OR (diabetes) OR (human immunodeficiency virus) OR (inflammatory disease) OR (vasculitis)) AND ((Psychiatric disorders) OR (somatoform disorders)) AND ((anticoagulant) OR (coumadin)) AND ((bleeding dyscrasia) OR (coagulopathy) OR (platelet count)))"}
{"candidate_id": "LLM04625", "doc_id": "NCT01602081_inc", "case_bucket": "or", "source_criterion": "Persistent primary or recurrent trans-sphincteric anal fistula", "candidate_expression": "(trans-sphincteric anal fistula primary recurrent)"}
```
