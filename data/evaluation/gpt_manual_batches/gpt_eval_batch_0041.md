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
{"candidate_id": "LLM01001", "doc_id": "NCT02951754_inc", "case_bucket": "other", "source_criterion": "White Brazilian of European descent Fulfillment of the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, (DSM-IV) diagnostic criteria for ADHD Eligibility to immediate-release MPH (IR-MPH) treatment", "candidate_expression": "((ADHD Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, (DSM-IV) diagnostic criteria) AND (Brazilian) AND (European descent) AND (White) AND (immediate-release MPH (IR-MPH) Eligibility))"}
{"candidate_id": "LLM01002", "doc_id": "NCT03046108_inc", "case_bucket": "other", "source_criterion": "Clinical suspicion of Morton neuroma confirmed in ultrasound scan Symptoms present more than six months The thickness of the nerve must be at least 2 mm in short axis and at least 5 mm in the longitudinal axis.", "candidate_expression": "((Morton neuroma Clinical suspicion) AND (Symptoms more than six months) AND (thickness of the nerve in short axis at least 2 mm) AND (thickness of the nerve in the longitudinal axis at least 5 mm) AND (ultrasound scan))"}
{"candidate_id": "LLM01003", "doc_id": "NCT00676273_exc", "case_bucket": "or", "source_criterion": "Patients: Who are pregnant or planning to become pregnant during the study or in the future With a elevated post-void residual (defined as PVR > 100cc) With a bleeding condition or on anti-coagulant therapy With immunosuppression (i.e. HIV, lymphoma) With multiple sclerosis or other progressive neurological disease With evidence of a local or systemic infection, including urinary tract infection With evidence of intrinsic sphincter deficiency as defined by a maximal urethral closure pressure of <20 cm H2O Previous sub-urethral sling Predominant overactive bladder symptoms", "candidate_expression": "((<20 cm H2O) AND (> 100cc) AND (PVR) AND (Predominant) AND (Previous) AND (anti-coagulant therapy) AND (bleeding condition) AND (elevated) AND (immunosuppression) AND (intrinsic sphincter deficiency) AND (maximal urethral closure pressure) AND (multiple sclerosis) AND (overactive bladder) AND (overactive bladder symptoms) AND (planning to become) AND (post-void residual) AND (progressive neurological disease) AND (sub-urethral sling) AND (urinary tract infection) AND ((local infection) OR (systemic infection)) AND ((pregnant)) AND ((during the study) OR (in the future)) AND ((HIV) OR (lymphoma)))"}
{"candidate_id": "LLM01004", "doc_id": "NCT02974686_exc", "case_bucket": "or", "source_criterion": "Dual organ or kidney after another solid organ transplant Presence of a preexisting significant GI condition that does not have a presumed causal relationship with MPA Evidence of any GI disorder induced by an infection, underlying medical condition, or concomitant medication other than MPA eGFR<40 ml/min at time of possible conversion Proteinuria >1 gram/day at time of possible conversion Hemoglobin <10 g/dL WBC <3 K/cumm Platelets <100 K/cumm Wound healing issues at time of possible conversion (eg, wound dehiscence, wound infection, incisional hernia, lymphocele, seroma) Elevated total cholesterol (>350 mg/dL) and/or triglycerides (>500 ng/dL) at time of possible conversion Hypersensitivity to everolimus, sirolimus, or other rapamycin deriviatives", "candidate_expression": "((GI condition preexisting significant) AND (Hemoglobin <10 g/dL) AND (Hypersensitivity) AND (Platelets <100 K/cumm) AND (Proteinuria >1 gram/day at time of possible conversion) AND (WBC <3 K/cumm) AND (Wound healing issues at time of possible conversion) AND (eGFR <40 ml/min at time of possible conversion) AND (infection) AND (solid organ transplant) AND (total cholesterol Elevated >350 mg/dL) AND (triglycerides >500 ng/dL at time of possible conversion) AND NOT (MPA) AND ((Dual kidney) OR (Dual organ)) AND ((incisional hernia) OR (lymphocele) OR (seroma) OR (wound dehiscence) OR (wound infection)) AND ((everolimus) OR (rapamycin) OR (sirolimus)) AND ((GI disorder induced by an infection) OR (medication) OR (underlying medical condition)))"}
{"candidate_id": "LLM01005", "doc_id": "NCT03223909_inc", "case_bucket": "or", "source_criterion": ">18 to < 90 years old Both sexes Mild to moderate tear film dysfunction clinical diagnose TBUT > 5 sec. and < 10 sec. Schirmer: > 4 mm and < 14 mm OSDI < 30 points Corneal staining < grade III on the Oxford scale Availability to go to each revision when indicated.", "candidate_expression": "((< 30 points) AND (< grade III) AND (> 4 mm and < 14 mm) AND (> 5 sec. and < 10 sec) AND (>18 to < 90 years) AND (Availability to go to each revision when indicated.) AND (Both sexes) AND (Corneal staining) AND (Mild) AND (OSDI) AND (Oxford scale) AND (Schirmer) AND (TBUT) AND (moderate) AND (old) AND (tear film dysfunction))"}
{"candidate_id": "LLM01006", "doc_id": "NCT02511574_inc", "case_bucket": "other", "source_criterion": "gestational age between 20 weeks and 23 weeks and 6 days singleton pregnancies", "candidate_expression": "((gestational age between 20 weeks and 23 weeks and 6 days) AND (singleton pregnancies))"}
{"candidate_id": "LLM01007", "doc_id": "NCT01943812_exc", "case_bucket": "or", "source_criterion": "endometrial thickness < 7 mm or no triple layer endometrium and/or functional follicles Uterine abnormality Chronic medical disease oocyte donation cycles", "candidate_expression": "((< 7 mm) AND (Chronic medical disease) AND (Uterine abnormality) AND (endometrial thickness) AND (no) AND (oocyte donation cycles) AND ((functional follicles) OR (triple layer endometrium)))"}
{"candidate_id": "LLM01008", "doc_id": "NCT03171987_inc", "case_bucket": "scope", "source_criterion": "All subjects underwent a detailed history and systemic physical examination including neurologic and musculoskeletal evaluations. To rule out any confounding etiologies, basic diagnostic laboratory tests including complete blood count and acute phase reactants (erythrocyte sedimentation rate and C-reactive protein) were performed. The patients diagnosed as having acute non-specific low back pain according to history and physical examinations were invited to participate and will be informed about the purpose and course of the study. A primary complaint of pain in the area between the 12th rib and buttock crease without leg pain Female or male, 20 - 80 years of age Low back pain of less than six weeks' duration; and at least moderate pain intensity (NRS<U+2267>4)", "candidate_expression": "((C-reactive protein) AND (Female) AND (Low back pain less than six weeks' duration) AND (NRS 4) AND (acute phase reactants) AND (age 20 - 80 years) AND (complete blood count) AND (diagnostic laboratory tests) AND (erythrocyte sedimentation rate) AND (history) AND (male) AND (non-specific low back pain acute) AND (pain area between the 12th rib and buttock crease) AND (pain intensity at least moderate) AND (physical examinations) AND NOT (leg pain))"}
{"candidate_id": "LLM01009", "doc_id": "NCT01205334_exc", "case_bucket": "or", "source_criterion": "Severe intercurrent infection Known HIV positivity Pregnant or lactating History of hypersensitivity reactions to murine protein-containing products.", "candidate_expression": "((HIV positivity) AND (Pregnant) AND (hypersensitivity reactions) AND (infection Severe intercurrent) AND (lactating) AND (murine) AND (murine protein-containing products))"}
{"candidate_id": "LLM01010", "doc_id": "NCT03147599_exc", "case_bucket": "or", "source_criterion": "Upper urinary tract deterioration Uncontrolled diabetes mellitus Evident local or pelvic recurrence Adjuvant chemotherapy Chronic retention Pouch stones Urethral stricture or urethro-ileal maldirection Sensitivity to Mebeverine Untreated chronic constipation Active symptomatic urinary infection", "candidate_expression": "((Adjuvant chemotherapy) AND (Chronic retention) AND (Mebeverine) AND (Pouch stones) AND (Sensitivity) AND (Upper urinary tract deterioration) AND (Urethral stricture) AND (chronic constipation Untreated Active) AND (diabetes mellitus Uncontrolled) AND (local recurrence) AND (pelvic recurrence) AND (urethro-ileal maldirection) AND (urinary infection symptomatic))"}
{"candidate_id": "LLM01011", "doc_id": "NCT02571881_inc", "case_bucket": "other", "source_criterion": "normal full term single pregnancy age 18 years or more BMI 20 - 35 kg/m2 written informed consent obtained", "candidate_expression": "((18 years or more) AND (20 - 35 kg/m2) AND (BMI) AND (age) AND (full term) AND (normal) AND (pregnancy) AND (single) AND (written informed consent obtained))"}
{"candidate_id": "LLM01012", "doc_id": "NCT00718952_exc", "case_bucket": "or", "source_criterion": "The other types of pulmonary hypertension. Subjects who refuse to subscribe written informed consents or can't cooperate with the trial well. Subjects with serious acute or chronic disease involved liver, kidney, and brain or have to use potent CYP3A4-inhibitor or nitrate to treat the underlying diseases. Subjects who are currently treated with sildenafil for PAH or taking sildenafil or tadalafil. Other contraindications in package insert.", "candidate_expression": "((CYP3A4-inhibitor) AND (PAH) AND (can't cooperate with the trial) AND (chronic disease involved brain) AND (chronic disease involved kidney) AND (chronic disease involved liver) AND (contraindications in package insert) AND (nitrate) AND (pulmonary hypertension other types) AND (refuse to subscribe written informed consents) AND (sildenafil) AND (tadalafil) AND (underlying diseases))"}
{"candidate_id": "LLM01013", "doc_id": "NCT02141061_exc", "case_bucket": "or", "source_criterion": "1. Subject is a post-menopausal woman, defined as either; six (6) months or more (immediately prior to screening visit) without a menstrual period, or prior hysterectomy and/or oophorectomy 2. Subject is pregnant or lactating or is attempting or expecting to become pregnant during the study 3. Women with abnormally high liver enzymes or liver disease. (ALT or AST exceeding 2.0 x ULN AND total bilirubin exceeding 1.5 x ULN at screening and confirmed on repeat). 4. Received an investigational drug in the 30 days prior to the screening for this study 5. Women with a history of PCOS 6. Concurrent use of any testosterone, progestin, androgen, estrogen, anabolic steroids, DHEA or hormonal products for at least 2 weeks prior to screening and during the study. 7. Use of oral contraceptives in the preceding 2 weeks. Use of Depo-Provera® in the preceding 10 months. 8. Has an IUD in place 9. Women currently using narcotics 10. Women currently taking spironolactone 11. Infectious disease screen is positive for HIV or Hepatitis A, B or C. 12. Clinically significant abnormal findings on screening examination or any condition which in the opinion of the investigator would interfere with the participant's ability to comply with the study instructions or endanger the participant if she took part in the study", "candidate_expression": "((Depo-Provera®) AND (IUD) AND (PCOS) AND (Women) AND (at screening) AND (during the study) AND (exceeding 1.5 x ULN) AND (exceeding 2.0 x ULN) AND (for at least 2 weeks prior to screening) AND (high) AND (history) AND (immediately prior to screening visit) AND (in the 30 days prior to the screening) AND (in the preceding 10 months) AND (in the preceding 2 weeks) AND (investigational drug) AND (is attempting or expecting to become pregnant during the study) AND (narcotics) AND (oral contraceptives) AND (post-menopausal) AND (prior) AND (screening) AND (six (6) months or more) AND (spironolactone) AND (the screening) AND (total bilirubin) AND (without) AND (woman) AND ((hysterectomy) OR (menstrual period) OR (oophorectomy)) AND ((lactating) OR (pregnant)) AND ((liver disease) OR (liver enzymes)) AND ((ALT) OR (AST)) AND ((DHEA) OR (anabolic steroids) OR (androgen) OR (estrogen) OR (hormonal products) OR (progestin) OR (testosterone)) AND ((HIV) OR (Hepatitis A) OR (Hepatitis B) OR (Hepatitis C)))"}
{"candidate_id": "LLM01014", "doc_id": "NCT00379366_exc", "case_bucket": "other", "source_criterion": "contra-indications of radiotherapy angioplasty with stenting", "candidate_expression": "((angioplasty with stenting) AND (contra-indications) AND (radiotherapy))"}
{"candidate_id": "LLM01015", "doc_id": "NCT02589353_inc", "case_bucket": "other", "source_criterion": "self-reported healthy adults between the ages of 18-60 who are fluent in English.", "candidate_expression": "((adults) AND (ages between 18-60) AND (fluent in English) AND (healthy self-reported))"}
{"candidate_id": "LLM01016", "doc_id": "NCT02788045_exc", "case_bucket": "or", "source_criterion": "Has chronic hepatitis B (measured by hepatitis B surface antigen test) or active hepatitis C (measured by hepatitis C virus [HCV] Ab test; if positive, HCV ribonucleic acid [RNA] PCR test will be used to confirm active versus past HCV infection), active syphilis infection, chlamydia, gonorrhea, or trichomonas . Active syphilis documented by serology unless positive serology is due to past treated infection Has had a thyroidectomy or active thyroid disease requiring medication during the last 12 months (not excluded: a stable thyroid supplementation) Has had major psychiatric illness and/or substance abuse problems during the past 12 months (including hospitalization or periods of work disability) that in the opinion of the investigator would preclude participation Has been in receipt of any licensed vaccine within 14 days prior to the first dose of study vaccine/placebo, plans to receive within 14 days after the first study vaccination, or plans to receive within 14 days before or after the second, third or fourth vaccination Is a recipient of a prophylactic or therapeutic HIV vaccine candidate at any time, or a recipient of other experimental vaccine(s) within the last 12 months. For participants who received an experimental vaccine (except HIV vaccine) more than 12 months ago, documentation of the identity of the experimental vaccine must be provided to the sponsor, who will determine eligibility on a case-by-case basis", "candidate_expression": "((Active) AND (HCV ribonucleic acid [RNA] PCR test) AND (HIV vaccine) AND (HIV vaccine candidate) AND (active) AND (active hepatitis C) AND (at any time) AND (case-by-case basis) AND (chlamydia) AND (chronic hepatitis B) AND (during the last 12 months) AND (during the past 12 months) AND (except) AND (experimental vaccine) AND (first study vaccination) AND (gonorrhea) AND (hepatitis B surface antigen test) AND (hepatitis C virus [HCV] Ab test) AND (hospitalization) AND (in the opinion of the investigator) AND (licensed vaccine) AND (major) AND (medication) AND (more than 12 months ago) AND (not excluded) AND (other experimental vaccine(s)) AND (placebo) AND (positive) AND (prophylactic) AND (psychiatric illness) AND (second, third or fourth vaccination) AND (serology) AND (stable) AND (study vaccination) AND (study vaccine) AND (substance abuse) AND (syphilis) AND (syphilis infection) AND (the first dose of study vaccine/placebo) AND (therapeutic) AND (thyroid disease) AND (thyroid supplementation) AND (thyroidectomy) AND (treated infection) AND (trichomonas) AND (unless) AND (vaccination) AND (within 14 days after) AND (within 14 days before or after) AND (within 14 days prior) AND (within the last 12 months) AND (work disability))"}
{"candidate_id": "LLM01017", "doc_id": "NCT02609698_exc", "case_bucket": "or", "source_criterion": "Patients with any contraindications or hypersensitivity related to antiplatelet therapy Patients with Acute Myocardial Infarction (ST elevation myocardial infarction, Non ST elevation myocardial infarction) Patients who are anticipated to receive treatment or surgery that may require desisting the administration of antiplatelet therapy for 2 weeks or longer during the period of the clinical trial Chronic total occlusion (CTO) lesions, in-stent restenosis (ISR) Patients experiencing cardiogenic shock Women who are breastfeeding, pregnant, or desiring pregnancy Patients with findings of hemorrhage Patients with a life expectancy of less than 1 year Patients who have received a drug-eluting stent (DES) procedure within the past 6 months Any other patients judged by the investigator to be unsuitable for the trial", "candidate_expression": "((Acute Myocardial Infarction) AND (CTO) AND (Chronic total occlusion) AND (DES) AND (ISR) AND (Non ST elevation myocardial infarction) AND (ST elevation myocardial infarction) AND (Women who are breastfeeding, pregnant, or desiring pregnancy) AND (antiplatelet therapy) AND (antiplatelet therapy for 2 weeks or longer) AND (cardiogenic shock) AND (contraindications) AND (drug-eluting stent procedure past 6 months) AND (hemorrhage) AND (hypersensitivity) AND (in-stent restenosis) AND (life expectancy less than 1 year) AND (surgery) AND (treatment))"}
{"candidate_id": "LLM01018", "doc_id": "NCT03063866_exc", "case_bucket": "or", "source_criterion": "Emergent condition like hematemesis. Patients with moderate to severe hepatic encephalopathy. Patients with hepatopulmonary syndrome. Patients with known or suspected hypersensitivity to the used medication were also excluded from the study.", "candidate_expression": "((Emergent condition) AND (hematemesis moderate severe) AND (hepatic encephalopathy) AND (hepatopulmonary syndrome known suspected) AND (hypersensitivity) AND (used medication))"}
{"candidate_id": "LLM01019", "doc_id": "NCT02595190_inc", "case_bucket": "or", "source_criterion": "1. Diagnosed with symptomatic sacral perineurial cysts(e.g., lumbosacral or perineal pain, fecal or urinary functions change, sexual function change, lower limb radiation pain, muscle abate, paresthesia, etc) 2. Visual analog scale more than or equal to 4 3. Signed the informed consent 4. Years, range 18-60 5. Self-rating anxiety scale (SAS) and self-rating depression scale (SDS) scores < 50 6. No Congenital,Mental and other Nervous system diseases 7. No Serious Cardiac,Pulmonary,Hepatic and Nephritic disease 8. No history of drug allergy 9. No pain(including dysmenorrhea) or drug use (e.g., antipyretics,sleeping pills) within the last month 10. MRI finding of sacral perineurial cysts, but without any clinical symptoms, included in the negative control group 11. MRI finding healthy volunteers don't have sacral perineurial cysts, included in the negative control groupblank control group", "candidate_expression": "((18-60) AND (Cardiac) AND (Cardiac,Pulmonary,Hepatic) AND (Congenital diseases) AND (Hepatic) AND (MRI finding healthy volunteers don't have sacral perineurial cysts, included in the negative control groupblank control group) AND (Mental disease) AND (Nephritic disease) AND (Nervous system diseases) AND (No) AND (Pulmonary) AND (SAS) AND (SDS) AND (Self-rating anxiety scale) AND (Signed the informed consent) AND (Visual analog scale) AND (Years) AND (allergy) AND (drug) AND (dysmenorrhea) AND (functions change, fecal) AND (last month) AND (lower limb radiation pain) AND (lumbosacral pain) AND (more than or equal to 4) AND (muscle abate) AND (pain) AND (paresthesia) AND (perineal pain) AND (sacral perineurial cysts() AND (scores < 50) AND (self-rating depression scale) AND (sexual function change) AND (symptomatic) AND (urinary functions change))"}
{"candidate_id": "LLM01020", "doc_id": "NCT02429583_inc", "case_bucket": "other", "source_criterion": "Willing to receive three doses of an FDA-approved Hepatitis B vaccine Volunteer chronically infected with HCV (as demonstrated by serology and/or viral load laboratory studies) Healthy volunteer without significant medical problems", "candidate_expression": "((HCV infected chronically) AND (Willing to receive three doses of an FDA-approved Hepatitis B vaccine) AND (volunteer Healthy))"}
{"candidate_id": "LLM01021", "doc_id": "NCT02109081_exc", "case_bucket": "or", "source_criterion": "1) preoperative diagnosis of delirium or dementia; 2) MMSE score of = 20 out of 30 on preoperative testing (more than mild cognitive impairment) or delirium on preoperative CAM testing; 3) language barriers that would preclude testing; 4) preoperative steroid use within 3 days of surgery; or 5) anticipation of postoperative intubation.", "candidate_expression": "((CAM testing preoperative) AND (MMSE score = 20 out of 30) AND (cognitive impairment more than mild) AND (delirium) AND (dementia) AND (intubation anticipation postoperative) AND (language barriers) AND (steroid preoperative within 3 days of surgery) AND (surgery))"}
{"candidate_id": "LLM01022", "doc_id": "NCT02652572_inc", "case_bucket": "or", "source_criterion": "1. Age 18 years or older 2. Diagnosis of venous leg ulcer(s), as clinically determined by the investigator by a positive venous reflux test (venous refilling <20 seconds) using Doppler ultrasound for at least 4 weeks prior to screening day, which have not adequately responded to conventional ulcer therapy. 3. Designated venous leg ulcer meets the following criteria at both the screening and baseline visits. If the patient has multiple ulcers, at least one ulcer must meet the following criteria at both the screening and baseline visits: 1. Present for at least 4 weeks 2. CEAP Classification Stage 6 3. Surface ulcer with an area > 15cm2 post debridement 4. Viable, granulating wound (investigator discretion) 4. Ulcers that extend through the epidermis but not through the muscle, tendon, or bone (Stage II or III ulcers as defined by the IAET). 5. Female patients of childbearing potential must have a negative pregnancy test at screening and must agree to use hormonal contraceptive, intrauterine device, diaphragm with spermicide, condom with spermicide, or abstinence throughout until 2 weeks after the last administration of study drug 6. Signed informed consent", "candidate_expression": "((Age 18 years or older) AND (CEAP Classification Stage 6 Present) AND (Doppler ultrasound at least 4 weeks prior to screening day) AND (Female) AND (IAET Stage II or III) AND (Signed informed consent) AND (Surface ulcer) AND (Ulcers) AND (area post debridement > 15cm2) AND (childbearing potential) AND (conventional ulcer therapy responded) AND (investigator discretion) AND (ulcer at least one) AND (ulcers) AND (ulcers multiple) AND (venous leg ulcer) AND (venous leg ulcer(s)) AND (venous refilling <20 seconds) AND (venous reflux test positive) AND (wound Viable granulating) AND ((extend through the epidermis) OR NOT (extend through the muscle) OR NOT (extend through the tendon) OR NOT (extend through the bone)) AND ((abstinence) OR (condom with spermicide) OR (diaphragm with spermicide) OR (hormonal contraceptive) OR (intrauterine device) OR (pregnancy test negative at screening)))"}
{"candidate_id": "LLM01023", "doc_id": "NCT02624908_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes Known peripheral artery disease Liver enzymes equal or more than 1.5 times the upper limit of normal Chronic heart failure NYHA class III or IV Current haemodialysis or peritoneal dialysis End stage liver disease, defined as acute or chronic liver disease and recent history of one of the following: ascites, encephalopathy, variceal bleeding, bilirubin equal or greater than 2.0 mg/dL, albumin equal or less than 3.5 g/ dL, prothrombin time greater or equal to 4 seconds, INR greater than or equal to 1.7 or prior liver transplant Known or suspected hypersensitivity to trial products or related products Female of child-bearing potential who is pregnant, breast-feeding or intends to become pregnant or is not using adequate contraceptive methods as required by law or local practice. Expected simultaneous participation in any other clinical trial of an investigational medicinal product. Receipt of any investigational medicinal product within 30 days before randomization Current or past (within the last 5 years) malignant neoplasms (except basal cell and squamous cell skin carcinoma) Any condition that in the investigator's opinion would make the subject unable to adhere to the trial visit schedule and procedures Known history of non-compliance to treatment.", "candidate_expression": "((Any condition that in the investigator's opinion would make the subject unable to adhere to the trial visit schedule and procedures) AND (Chronic heart failure) AND (End stage liver disease) AND (Female of child-bearing potential who is pregnant, breast-feeding or intends to become pregnant or is not using adequate contraceptive methods as required by law or local practice.) AND (INR greater than or equal to 1.7) AND (Liver enzymes equal or more than 1.5 times the upper limit of normal) AND (NYHA class III or IV) AND (Type 1 diabetes) AND (acute liver disease) AND (albumin equal or less than 3.5 g/ dL) AND (ascites) AND (basal cell carcinoma) AND (bilirubin equal or greater than 2.0 mg/dL) AND (chronic liver disease) AND (encephalopathy) AND (haemodialysis) AND (hypersensitivity) AND (liver transplant prior Known suspected) AND (malignant neoplasms Current past within the last 5 years) AND (peripheral artery disease) AND (peritoneal dialysis) AND (prothrombin time greater or equal to 4 seconds) AND (related products) AND (squamous cell skin carcinoma) AND (trial products) AND (variceal bleeding))"}
{"candidate_id": "LLM01024", "doc_id": "NCT03631355_inc", "case_bucket": "other", "source_criterion": "Patients undergoing a high tibial osteotomy (HTO) Patients undergoing tibial tubercle osteotomy (TTO) with or without medial patello-femoral ligament (MPFL) reconstruction", "candidate_expression": "((high tibial osteotomy (HTO) undergoing) AND (medial patello-femoral ligament (MPFL) reconstruction) AND (tibial tubercle osteotomy (TTO) undergoing))"}
{"candidate_id": "LLM01025", "doc_id": "NCT03013790_exc", "case_bucket": "or", "source_criterion": "Patients with head trauma or Neurosurgical intervention Patients <65 years of age Patients with an expected life expectancy <48 hours Blind patients Patients with a seizure history Patients with uncontrolled hypertension Patients with a supratheraputic (>3.0) INR Patients on strong CYP1A2 inhibitors: ciprofloxacin, fluvoxamine, methoxsalen, ofloxacin, primaquine Patients who do not speak English or Spanish", "candidate_expression": "((Blind) AND (INR supratheraputic >3.0) AND (Neurosurgical intervention) AND (age <65 years) AND (ciprofloxacin) AND (expected life expectancy <48 hours) AND (fluvoxamine) AND (head trauma) AND (methoxsalen) AND (ofloxacin) AND (primaquine) AND (seizure history) AND (speak English) AND (speak Spanish) AND (strong CYP1A2 inhibitors) AND (uncontrolled hypertension))"}
```
