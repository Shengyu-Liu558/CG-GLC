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
{"candidate_id": "LLM07051", "doc_id": "NCT02396420_inc", "case_bucket": "or", "source_criterion": "Patient has provided signed informed consent Patient is aged greater than or equal to 40 and less than or equal to 89 years of age Patient has a prostate size between 90g and 200g, as determined by MRI Patient has experienced lower urinary tract symptoms (LUTS) for at least 6 months prior to study enrollment Patient has an IPSS score of at least 13 at baseline Patient is either: refractory to medical treatment, contraindicated to medical treatment, OR refuses medical treatment Patient either: refuses surgical treatment OR is contraindicated for surgical treatment Patient meets ONE of the following criteria: baseline PSA < 4.0ng/mL (no prostate biopsy required) OR baseline PSA >/= 4 ng/mL AND a negative prostate biopsy (minimum 12 core biopsy) within the prior 12 months", "candidate_expression": "((< 4.0ng/mL) AND (>/= 4 ng/mL) AND (IPSS score) AND (MRI) AND (PSA) AND (aged) AND (at baseline) AND (at least 13) AND (at least 6 months prior to study enrollment) AND (baseline) AND (between 90g and 200g) AND (core biopsy) AND (greater than or equal to 40) AND (less than or equal to 89 years) AND (lower urinary tract symptoms (LUTS)) AND (minimum 12) AND (negative) AND (prostate biopsy) AND (prostate size) AND (signed informed consent) AND (study enrollment) AND (within the prior 12 months) AND ((contraindicated to medical treatment) OR (refractory to medical treatment) OR (refuses medical treatment)) AND ((contraindicated for surgical treatment) OR (refuses surgical treatment)))"}
{"candidate_id": "LLM07052", "doc_id": "NCT01743755_exc", "case_bucket": "or", "source_criterion": "Immunocompromised patients: Patients with a known congenital or acquired immunodeficiency. Patients who received chemotherapy less than 6 weeks ago. Patients who received corticosteroids in the last 6 weeks. Patients who received immunosuppressive medication in the last 6 weeks (e.g. cyclosporin, cyclophosphamide, azathioprine). Patients with chronic obstructive pulmonary disease who are on systemic corticosteroids. Patients who require intensive care unit treatment. Patients with tropical worm infection. Patients with dexamethasone intolerance. Pregnant and breastfeeding women.", "candidate_expression": "((Immunocompromised) AND (Pregnant and breastfeeding women) AND (chemotherapy) AND (chronic obstructive pulmonary disease) AND (corticosteroids) AND (dexamethasone) AND (immunodeficiency) AND (immunosuppressive medication) AND (in the last 6 weeks) AND (intensive care unit) AND (intolerance) AND (less than 6 weeks ago) AND (systemic corticosteroids) AND (tropical worm infection) AND ((azathioprine) OR (cyclophosphamide) OR (cyclosporin)) AND ((acquired) OR (congenital)))"}
{"candidate_id": "LLM07053", "doc_id": "NCT01997580_exc", "case_bucket": "or", "source_criterion": "DSM-IV-TR substance-related disorders (except nicotine) significant medical or neurological conditions mental retardation or organic brain damage", "candidate_expression": "((DSM-IV-TR) AND (except) AND (mental retardation) AND (nicotine) AND (organic brain damage) AND (significant medical or neurological conditions) AND (substance-related disorders))"}
{"candidate_id": "LLM07054", "doc_id": "NCT01116882_inc", "case_bucket": "or", "source_criterion": "1. Subject is at least 18 years old. 2. Subject requires single- or multi-vessel percutaneous coronary intervention (PCI) of de novo or restenotic target lesion (including in-stent restenotic lesions). 3. Subject's lesion(s) is (are) amenable to stent treatment with currently available FDA-approved bare metal or drug eluting stents. 4. Subject is an acceptable candidate for elective, urgent or emergency coronary artery bypass graft (CABG). 5. Subject has clinical evidence of ischemic heart disease in terms of a positive functional study, or documented symptoms. 6. Documented stable angina pectoris [Canadian Cardiovascular Society Classification (CCS) 1, 2, 3, or 4], unstable angina pectoris with documented ischemia (Braunwald Class IB-C, IIB-C, or IIIB-C), non-ST segment elevation myocardial infarction, or documented silent ischemia. 7. Subject is willing and able to undergo percutaneous intervention at SOS hospital, if randomized to SOS study arm. 8. Subject and the treating physician agree that the subject will comply with all follow-up evaluations. 9. Subject has been informed of the nature of the study and agrees to its provisions and has provided written informed consent as approved by the Institutional Review Board/Ethics Committee of the respective clinical site. 10. The target lesion(s) is (are) de novo or restenotic (including in-stent restenotic) native coronary artery lesion(s) with greater than 50 and less than 100% stenosis (visual estimate), or the target lesion is an acute (less than 1 month) total occlusion as evidenced by clinical symptoms. 11. Target lesions(s) is (are) located in an infarct (if not treated with primary PCI) or non-infarct-related artery with a 70% or greater stenosis (by visual estimate) more than 72 hours following the ST segment elevation myocardial infarction (STEMI). Lesions treated with PCI more than 72 hours following STEMI would be subject to the same protocol inclusion/exclusion criteria listed above and below with the exception that a target lesion of 70% or greater stenosis may be treated with or without symptoms or abnormal stress test).", "candidate_expression": "((Braunwald Class IB-C, IIB-C, or IIIB-C) AND (Canadian Cardiovascular Society Classification (CCS) 1, 2, 3, or 4) AND (SOS hospital) AND (ST segment elevation myocardial infarction (STEMI)) AND (Subject and the treating physician agree that the subject will comply with all follow-up evaluations.) AND (Subject has been informed of the nature of the study and agrees to its provisions and has provided written informed consent as approved by the Institutional Review Board/Ethics Committee of the respective clinical site.) AND (Subject is willing and able to undergo percutaneous intervention at SOS hospital, if randomized to SOS study arm.) AND (Target lesions) AND (amenable to stent treatment) AND (coronary artery bypass graft (CABG)) AND (coronary artery lesion in-stent restenotic) AND (functional study positive) AND (in-stent restenotic lesions in-stent restenotic) AND (infarct) AND (ischemia documented) AND (ischemic heart disease clinical evidence) AND (old at least 18 years) AND (percutaneous coronary intervention (PCI)) AND (percutaneous intervention willing able) AND (stenosis) AND (stenosis 70% or greater) AND (stenosis greater than 50 and less than 100%) AND (stenosis more than 72 hours following the ST segment elevation myocardial infarction (STEMI)) AND (target lesion) AND (total occlusion clinical symptoms less than 1 month) AND NOT (primary PCI) AND ((de novo) OR (restenotic)) AND ((bare metal stents) OR (drug eluting stents)) AND ((elective) OR (emergency) OR (urgent)) AND ((non-ST segment elevation myocardial infarction) OR (silent ischemia documented silent) OR (stable angina pectoris stable) OR (unstable angina pectoris unstable)) AND ((multi-vessel) OR (single- vessel)) AND ((target lesion) OR (target lesion acute)) AND ((in an infarct -related artery) OR (non-infarct-related artery)))"}
{"candidate_id": "LLM07055", "doc_id": "NCT00679341_inc", "case_bucket": "or", "source_criterion": "Histologically or cytologically confirmed adenocarcinoma of the breast with locally advanced or metastatic disease, and a candidate for chemotherapy. Human epidermal growth factor receptor 2 (HER2)-positive. No prior chemotherapy for their metastatic breast cancer (MBC). Measurable disease. Age ≥ 18 years. For women of childbearing potential and men with partners of childbearing potential, agreement to use a highly effective, non-hormonal form of contraception or 2 effective forms of non-hormonal contraception by the patient and/or partner. Contraception use must continue for the duration of study treatment and for at least 6 months after the last dose of study treatment. Male patients whose partners are pregnant should use condoms for the duration of the study.", "candidate_expression": "((2) AND (Age) AND (Contraception) AND (Human epidermal growth factor receptor 2 (HER2)) AND (Male) AND (Measurable disease) AND (No) AND (adenocarcinoma of the breast) AND (candidate for chemotherapy) AND (chemotherapy) AND (childbearing potential) AND (condoms) AND (continue for the duration of study treatment) AND (disease locally advanced) AND (for at least 6 months after the last dose of study treatment) AND (for the duration of the study) AND (highly effective) AND (men) AND (metastatic breast cancer (MBC)) AND (metastatic disease) AND (non-hormonal) AND (partners are pregnant) AND (positive) AND (prior) AND (study treatment) AND (the last dose of study treatment) AND (with partners of childbearing potential) AND (women) AND (≥ 18 years) AND ((Histologically confirmed) OR (cytologically confirmed)) AND ((contraception) OR (non-hormonal contraception)))"}
{"candidate_id": "LLM07056", "doc_id": "NCT03089086_inc", "case_bucket": "or", "source_criterion": "South Australian secondary school students in years 10, 11, and 12 in 2017 Written parental consent for those under the age of 18 Written student consent assent for those under the age of 18 (or if 18 years old and older consent for themselves) Available at school for at least the first pharyngeal swab and willing to comply with study procedures", "candidate_expression": "((South Australian) AND (Written parental consent for those under the age of 18) AND (Written student consent assent for those under the age of 18 (or if 18 years old and older consent for themselves)) AND (comply with study procedures) AND (first) AND (in 2017) AND (pharyngeal swab) AND (secondary school students) AND (willing to) AND ((years 10) OR (years 11) OR (years 12)))"}
{"candidate_id": "LLM07057", "doc_id": "NCT02668016_exc", "case_bucket": "or", "source_criterion": "History of neuropathy Regularly taking prescribed analgesia History of a chronic pain condition History of severe mental illness (as their experience of symptoms may already be altered) Current use of fibrates (because of the risk of interaction with statins but will not exclude participants taking ezetimibe). Severe previous reaction or reaction considered immunological, such as anaphylaxis, facial swelling, severe rash, muscle ache with rise in serum creatine kinase, inflammatory myopathy, rhabdomyolysis or liver function abnormalities (aspartate transaminase (AST) or alanine transaminase (ALT) greater than 3 times upper limit or normal). Side-effects taking longer than 2 weeks to develop (because in such participants much longer blocks of treatment would be required, if the present study is positive such studies will be planned for the future)*. History of statin intolerance with drug interaction to antiretroviral drugs. History of statin intolerance to any other drug. Pregnant or breast feeding. Side effects taking longer than 2 weeks to present. In clinical judgement of study doctor, participant should not participate.", "candidate_expression": "((ALT) AND (AST) AND (Pregnant or breast feeding) AND (alanine transaminase) AND (analgesia Regularly) AND (anaphylaxis) AND (antiretroviral drugs) AND (aspartate transaminase) AND (chronic pain) AND (facial swelling,) AND (fibrates) AND (inflammatory myopathy) AND (intolerance) AND (liver function abnormalities) AND (mental illness severe) AND (muscle ache) AND (neuropathy) AND (rhabdomyolysis) AND (serum creatine kinase rise) AND (severe rash) AND (statin))"}
{"candidate_id": "LLM07058", "doc_id": "NCT02900443_exc", "case_bucket": "or", "source_criterion": "Overlap syndrome with Primary Sclerosing Cholangitis (PSC) or Primary Biliary Cholangitis (PBC) (Paris criteria, strong positive Anti-Mitochondrial Antibodies (AMA), past liver biopsy or cholangiographic findings compatible with PBC or PSC). Presentation with acute liver failure, defined as presence of hepatic encephalopathy and coagulopathy (INR > 1.5) Current treatment with prednisone/prednisolone and/or immunosuppressive medication for an indication other than autoimmune hepatitis Current systemic infection Other clinically significant medical conditions that could interfere with the trial If female of childbearing potential: known pregnancy, or unwilling to practice anticontraceptive measures. History of noncompliance with medical regimens, or patients who are considered to be potentially unreliable or unable to participate Mental instability or incompetence, such that the validity of informed consent or compliance with the trial is uncertain", "candidate_expression": "((> 1.5) AND (AMA) AND (Anti-Mitochondrial Antibodies) AND (History of noncompliance with medical regimens, or patients who are considered to be potentially unreliable or unable to participate) AND (INR) AND (Mental instability or incompetence, such that the validity of informed consent or compliance with the trial is uncertain) AND (Overlap syndrome) AND (PBC) AND (PSC) AND (Paris criteria,) AND (acute liver failure) AND (autoimmune hepatitis) AND (coagulopathy) AND (f female of childbearing potential: known pregnancy, or unwilling to practice anticontraceptive measures) AND (hepatic encephalopathy) AND (indication) AND (other) AND (strong positive) AND (systemic infection) AND ((cholangiographic findings) OR (liver biopsy)) AND ((immunosuppressive medication) OR (prednisolone) OR (prednisone)) AND ((Primary Biliary Cholangitis) OR (Primary Sclerosing Cholangitis)))"}
{"candidate_id": "LLM07059", "doc_id": "NCT02208739_inc", "case_bucket": "or", "source_criterion": "Patients should have at least 12 teeth present Patients with Moderate to Advanced Chronic periodontitis Patients with 2 or more interproximal sites (not on same tooth) with probing pocket depths of 5mm or more and 2 or more interproximal sites (not on same tooth)of probing attachment loss of 4mm or more which bled on probing.", "candidate_expression": "((2 or more) AND (4mm or more) AND (5mm or more) AND (Advanced) AND (Chronic periodontitis) AND (Moderate) AND (at least 12) AND (bled on probing) AND (interproximal sites of probing attachment loss of 4mm or more) AND (interproximal sites with probing pocket depths of 5mm or more) AND (probing) AND (teeth present))"}
{"candidate_id": "LLM07060", "doc_id": "NCT02985710_inc", "case_bucket": "or", "source_criterion": "Males and females with confirmed disease: Fabry (by GLA enzymes and/or DNA testing) naïve and on ERT, Mitochondrial diseases (electron transport chain and/or DNA testing) or connective tissue diseases (clinical criteria and/or DNA testing when available) Consenting adults (18 years and older) who agrees and consents to skin biopsy and QSART procedure", "candidate_expression": "((Consenting adults (18 years and older) who agrees and consents to skin biopsy and QSART procedure) AND (ERT) AND (confirmed disease Fabry naïve) AND ((Males) OR (females)) AND ((Mitochondrial diseases) OR (connective tissue diseases)) AND ((DNA testing) OR (electron transport chain)) AND ((DNA testing) OR (clinical criteria)) AND ((DNA testing) OR (GLA enzymes)))"}
{"candidate_id": "LLM07061", "doc_id": "NCT02360631_exc", "case_bucket": "or", "source_criterion": "Renal impairment Evidence or history of clinically significant allergic reactions to varenicline A cardiovascular event in the past month History of alcohol or drug dependence in the past year Major depressive disorder in the last year requiring treatment History of panic disorder, psychosis, bipolar disorder, or eating disorders Use of tobacco products other than cigarettes in past 30 days Use of pharmacotherapy in the month prior to enrollment, including prior use of varenicline Pregnant, contemplating getting pregnant, or breastfeeding Plans to move from Kansas City during the treatment and follow-up phase Another household member enrolled in the study Evidence of current severe major depressive disorder or suicidal ideation", "candidate_expression": "((Major depressive disorder last year) AND (Pregnant, contemplating getting pregnant, or breastfeeding) AND (Renal impairment) AND (Use of tobacco past 30 days) AND (allergic) AND (cardiovascular event in the past month) AND (other than cigarettes) AND (pharmacotherapy month prior to enrollment) AND (treatment) AND (varenicline) AND ((bipolar disorder) OR (eating disorders) OR (panic disorder) OR (psychosis)) AND ((major depressive disorder severe) OR (suicidal ideation)) AND ((alcohol dependence) OR (drug dependence)))"}
{"candidate_id": "LLM07062", "doc_id": "NCT03249272_exc", "case_bucket": "or", "source_criterion": "Decompensated heart failure or hemodynamic instability Prior coronary revascularization (PCI or CABG) or myocardial infarction (as evidenced by previously elevated CPK-MB or troponin levels) Accelerating angina or unstable angina Inability to physically tolerate MRI or implanted objects that are MRI incompatible Inability to provide written informed consent obtained at time of study enrollment. Severe claustrophobia Advanced heart block or sinus node dysfunction Hypersensitivity or allergic reaction to regadenoson or adenosine Hypotension Active bronchospasm or history of hospitalization due to bronchospasm History of seizures Recent cerebrovascular accident Use of dipyridamole within the last 5 days Contraindication to aminophylline Severe renal insufficiency with estimated glomerular filtration rate <30 ml/min/ 1.73 m2 Pregnant or nursing", "candidate_expression": "((Contraindication) AND (Hypotension) AND (Inability to physically tolerate) AND (Inability to provide written informed consent obtained at time of study enrollment.) AND (aminophylline) AND (bronchospasm) AND (cerebrovascular accident Recent) AND (claustrophobia Severe) AND (dipyridamole within the last 5 days) AND (estimated glomerular filtration rate <30 ml/min/ 1.73 m2) AND (renal insufficiency Severe) AND (seizures History) AND ((Accelerating angina) OR (unstable angina)) AND ((MRI) OR (implanted objects MRI incompatible)) AND ((heart failure Decompensated) OR (hemodynamic instability)) AND ((heart block) OR (sinus node dysfunction)) AND ((Hypersensitivity) OR (allergic)) AND ((adenosine) OR (regadenoson)) AND ((bronchospasm Active) OR (hospitalization history)) AND ((coronary revascularization Prior) OR (myocardial infarction Prior)) AND ((Pregnant) OR (nursing)) AND ((CABG) OR (PCI)) AND ((CPK-MB levels) OR (troponin levels)))"}
{"candidate_id": "LLM07063", "doc_id": "NCT02117986_inc", "case_bucket": "other", "source_criterion": "patient hospitalized in critical care units patient infected by multi drug resistant Gram negative bacteria susceptibly only to colistin source of infection: blood, respiratory, intra abdominal or urinary", "candidate_expression": "((Gram negative bacteria multi drug resistant susceptibly) AND (colistin only) AND (critical care units) AND (hospitalized))"}
{"candidate_id": "LLM07064", "doc_id": "NCT03083197_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to tetracycline, doxycycline or azithromycin Administration of doxycycline, azithromycin, chloramphenicol, rifampicin, or tetracycline during the preceding 7 days Pregnancy or breast-feeding Patients with myasthenia gravis or systemic lupus erythematosus Patients with an established infection (diagnostic test required) e.g. acute malaria, dengue, leptospirosis, typhoid, Japanese encephalitis etc. Current TB or TB treatment in = 6 months (contain active antibiotics against Orientia spp.) Current HAART use for HIV, long term use of immunosuppressants (e.g. steroids, chemotherapy, TNF-inhibitors and related agents) Patients with severe disease whom the clinical team feel their condition necessitates the need for additional scrub typhus treatment beyond the allocated antibiotic treatment assigned at randomization (e.g. IV chloramphenicol and/or PO/NG rifampicin)", "candidate_expression": "((HAART) AND (HIV) AND (Japanese encephalitis) AND (Pregnancy) AND (TB) AND (TB treatment in = 6 months) AND (TNF-inhibitors) AND (acute malaria) AND (azithromycin) AND (breast-feeding) AND (chemotherapy) AND (chloramphenicol) AND (dengue) AND (diagnostic test) AND (doxycycline) AND (hypersensitivity) AND (immunosuppressants long term use) AND (infection) AND (leptospirosis) AND (myasthenia gravis) AND (rifampicin) AND (steroids) AND (systemic lupus erythematosus) AND (tetracycline) AND (typhoid))"}
{"candidate_id": "LLM07065", "doc_id": "NCT02695992_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure Ischemic heart disease Hypotension (Systolic blood pressure <100 mmHg) Treatment with class I or III antiarrhythmic drugs Severe hepatic or renal failure Pregnancy or lactation Hypersensitivity or contradictions to study drugs Atrio-ventricular conduction disturbances Thyrotoxicosis Life limiting disease or substance abuse which may affect participation", "candidate_expression": "((<100 mmHg) AND (Atrio-ventricular conduction disturbances) AND (Congestive heart failure) AND (Hypersensitivity) AND (Hypotension) AND (Ischemic heart disease) AND (Life limiting disease) AND (Pregnancy) AND (Severe) AND (Systolic blood pressure) AND (Thyrotoxicosis) AND (antiarrhythmic drugs) AND (class I) AND (class III) AND (contradictions) AND (hepatic failure) AND (lactation) AND (may affect participation) AND (renal failure) AND (study drugs) AND (substance abuse))"}
{"candidate_id": "LLM07066", "doc_id": "NCT03216967_exc", "case_bucket": "or", "source_criterion": "Known proved BKV nephropathy Hypersensitivity to everolimus, sirolimus or excipient Concomitant treatment by leflunomide, cidofovir, sirolimus, Millepertuis (Hypericum Perforatum) Pregnant or lactating women Women of child bearing potential unless they are using a birth control method", "candidate_expression": "((BKV nephropathy) AND (Concomitant) AND (Hypericum Perforatum) AND (Hypersensitivity) AND (Women) AND (birth control method) AND (child bearing potential) AND (proved) AND (unless) AND (women) AND ((Millepertuis) OR (cidofovir) OR (leflunomide) OR (sirolimus)) AND ((Pregnant) OR (lactating)) AND ((everolimus) OR (excipient) OR (sirolimus)))"}
{"candidate_id": "LLM07067", "doc_id": "NCT03034096_inc", "case_bucket": "or", "source_criterion": "Lobectomy or pneumonectomy Esophagectomy Radical (total) cystectomy Pancreatectomy Partial hepatectomy Hyperthermic intraperitoneal chemotherapy (HIPEC) Gastrectomy (subtotal or total) Cholecystectomy or bile duct resection", "candidate_expression": "((Cholecystectomy) AND (Esophagectomy) AND (Gastrectomy subtotal total) AND (HIPEC) AND (Hyperthermic intraperitoneal chemotherapy) AND (Lobectomy) AND (Pancreatectomy) AND (Partial hepatectomy) AND (Radical cystectomy) AND (bile duct resection) AND (pneumonectomy) AND (total cystectomy))"}
{"candidate_id": "LLM07068", "doc_id": "NCT02510404_inc", "case_bucket": "or", "source_criterion": "1. Diagnosis of primary immunodeficiency with established plan to undergo myeloablative or non-myeloablative allogeneic hematopoietic stem cell transplant for treatment thereof or diagnosis of a form of primary immunodeficiency for which hematopoietic stem cell transplantation is not indicated. 2. Active infection with EBV, CMV, and/or Adenovirus, unable to be successfully controlled with standard therapy. 3. Steroids less than 0.5 mg/kg/day prednisone 4. Karnofsky/Lansky score of ≥ 50 5. ANC greater than 500/µL. 6. Bilirubin <2x, AST <3x, Serum creatinine <2x upper limit of normal, Hgb >8.0 7. Pulse oximetry of > 90% on room air 8. Negative pregnancy test (if female of childbearing potential) 9. Patient or parent/guardian capable of providing informed consent.", "candidate_expression": "((ANC greater than 500/µL) AND (AST <3x) AND (Bilirubin <2x) AND (Hgb >8.0) AND (Karnofsky/Lansky score ≥ 50) AND (Patient or parent/guardian capable of providing informed consent) AND (Pulse oximetry on room air > 90%) AND (Serum creatinine <2x upper limit of normal) AND (Steroids) AND (childbearing potential) AND (female) AND (prednisone less than 0.5 mg/kg/day) AND (pregnancy test Negative) AND (standard therapy unable to be controlled) AND NOT (hematopoietic stem cell transplantation) AND ((primary immunodeficiency)) AND ((allogeneic hematopoietic stem cell transplant myeloablative) OR (non-myeloablative allogeneic hematopoietic stem cell transplant)) AND ((Adenovirus) OR (CMV) OR (EBV)))"}
{"candidate_id": "LLM07069", "doc_id": "NCT01980680_exc", "case_bucket": "other", "source_criterion": "Patients with >14 follicles on day of trigger Previous hyperresponse with OHSS development Previous low response (less than 3 oocytes on a high dose of FSH stimulation) Endocrine disorders", "candidate_expression": "((Endocrine disorders) AND (follicles >14 on day of trigger) AND (high dose of FSH stimulation) AND (hyperresponse Previous OHSS development) AND (low response Previous) AND (oocytes less than 3))"}
{"candidate_id": "LLM07070", "doc_id": "NCT02635893_inc", "case_bucket": "or", "source_criterion": "Male and females between ages 18-85 years of age SCI ( =1 month of injury) ASIA A, B,C and D SCI above L5 Able to perform a visible contraction with dorsiflexor and hip flexor muscles (allowing testing of largely impaired patients) Able to ambulate a few steps with or without an assistive device Male and females between ages 18-85 years of age Able to walk and complete lower-limb tests with both legs", "candidate_expression": "((=1 month of injury) AND (A, B,C and D) AND (ASIA) AND (Able to ambulate a few steps) AND (Able to complete lower-limb tests) AND (Able to walk) AND (Male) AND (SCI) AND (above L5) AND (ages) AND (between 18-85 years of age) AND (females) AND (l) AND (with assistive device) AND (with both legs) AND (without an assistive device))"}
{"candidate_id": "LLM07071", "doc_id": "NCT02823808_exc", "case_bucket": "or", "source_criterion": "The use of weight-lowering drugs, any investigational blood-glucose or lipid-lowering agent (other than statins or ezetimibe) within the past 3 months Previous treatment with systemic corticosteroids or a change in dosage of thyroid hormones in the previous 6 weeks The use of insulin within the 3 months prior to screening Others", "candidate_expression": "((agent) AND (blood-glucose) AND (change in dosage) AND (drugs) AND (ezetimibe) AND (insulin) AND (investigational) AND (lipid-lowering) AND (other) AND (past 3 months) AND (previous 6 weeks) AND (screening) AND (statins) AND (systemic corticosteroids) AND (thyroid hormones) AND (weight-lowering) AND (within the 3 months prior to screening))"}
{"candidate_id": "LLM07072", "doc_id": "NCT01720394_inc", "case_bucket": "or", "source_criterion": "medical indication for induction of labor 18 years of age signed informed consent cephalic presentation no PROM 37+0 - 42+0 weeks of gestation Bishop-Score = 6 no contra-indication for medical induction of labor no clinical signs of infection", "candidate_expression": "((18 years) AND (37+0) AND (42+0) AND (= 6) AND (Bishop-Score) AND (PROM) AND (age) AND (cephalic presentation) AND (clinical signs of) AND (contra-indication) AND (induction of labor) AND (infection) AND (medical indication) AND (medical induction of labor) AND (no) AND (signed informed consent) AND (weeks of gestation))"}
{"candidate_id": "LLM07073", "doc_id": "NCT02536976_exc", "case_bucket": "or", "source_criterion": "Known or suspected alcohol or substance abuse in the preceding 12 months. Women who are pregnant or breastfeeding. Women of childbearing potential (WOCP) who are not using at least one method of contraception. Patients with severe renal impairment (CLcr = 29 mL/min, or eGFR = 29 mL/min/1.73 m2), or moderate or severe hepatic impairment (Child-Pugh classes B or C). Patients with bladder outlet obstruction (BOO) that, in the opinion of the study urologist, would expose them to risk of urinary retention during treatment with mirabegron. Patients treated with drugs metabolized by the CYP2D6 pathway. Patients with supine systolic blood pressure (SBP) = 180 mm Hg, or diastolic blood pressure (DBP) = 110 mm Hg. Clinically significant, uncontrolled cardiac arrhythmia, unstable angina, congestive heart failure (NYHA Class 3 or 4), or history of myocardial infarction in the preceding 2 years. History of cancer in the preceding 2 years other than successfully treated, non-metastatic, squamous cell or basal cell carcinoma, or cervical cancer in situ. Any major urological procedure in the preceding 90 days. Any major surgical procedure in the preceding 30 days. Previously treated with mirabegron within 60 days prior to the baseline visit (Visit 2), or previously having failed treatment with mirabegron regardless of duration and timing of treatment. Current or previous, within the 60 days preceding the baseline visit (Visit 2), treatment with antimuscarinic agents for OAB symptoms; and, willingness to not use antimuscarinic agents for the duration of the study. Currently receiving any other investigational drug or having received an investigational drug within the 60 days preceding the baseline visit (Visit 2). Any condition or laboratory test result, which, in the opinion of the Investigator or the Study Urologist, might result in an increased risk to the patient, or would affect their participation in the study. Any patient who, in the opinion of the Investigator, is not a good candidate for the study or will not be able to follow study procedures.", "candidate_expression": "((3) AND (4) AND (= 110 mm Hg) AND (= 180 mm Hg) AND (= 29 mL/min) AND (= 29 mL/min/1.73 m2) AND (B) AND (BOO) AND (C) AND (CLcr) AND (Child-Pugh classes) AND (Currently receiving any other investigational drug or having received an investigational drug within the 60 days preceding the baseline visit (Visit 2)) AND (DBP) AND (NYHA Class) AND (OAB symptoms) AND (SBP) AND (Women of childbearing potential (WOCP) who are not using at least one method of contraception) AND (Women who are pregnant or breastfeeding) AND (alcohol abuse) AND (antimuscarinic agents) AND (basal cell carcinoma) AND (baseline visit) AND (bladder outlet obstruction) AND (cancer) AND (carcinoma squamous cell) AND (cardiac arrhythmia) AND (cervical cancer in situ) AND (congestive heart failure) AND (diastolic blood pressure) AND (eGFR) AND (hepatic impairment) AND (major surgical procedure) AND (major urological procedure) AND (mirabegron) AND (moderate) AND (myocardial infarction) AND (non-metastatic) AND (other) AND (preceding 12 months) AND (preceding 2 years) AND (preceding 30 days) AND (preceding 90 days) AND (renal impairment) AND (risk of urinary retention) AND (severe) AND (substance abuse) AND (successfully treated) AND (supine) AND (systolic blood pressure) AND (uncontrolled) AND (unstable angina) AND (willingness to not use antimuscarinic agents for the duration of the study) AND (within 60 days prior to the baseline visit) AND (within the 60 days preceding the baseline visit))"}
{"candidate_id": "LLM07074", "doc_id": "NCT01799681_inc", "case_bucket": "other", "source_criterion": "diagnosed with PD by a neurologist (Fahn and Elton, 1987); aged 30 to 85 years; at modified Hoehn and Yahr (H&Y) stage 1.5 to 3 (Hoehn and Yahr ,1967; Goetz et al., 2004); able and willing to give written consent for participation in the study; living at home in the community; able to walk independently for 30 metres with or without an assistive device.", "candidate_expression": "((PD by a neurologist) AND (able and willing to give written consent for participation in the study;) AND (able to walk independently with or without an assistive device for 30 metres) AND (aged 30 to 85 years) AND (living at home in the community) AND (modified Hoehn and Yahr (H&Y) stage 1.5 to 3))"}
{"candidate_id": "LLM07075", "doc_id": "NCT02944929_inc", "case_bucket": "or", "source_criterion": "Males and females aged between 18 to 75 years. Adult patient under guardianship with consent obtained and the legal guardian's authorisation obtained. Single stroke having occurred more than 6 months before (previous TIA is accepted). Capable of understanding instructions and participating in the definition of a therapeutic goal (Boston Diagnostic Aphasia Examination (BDAE) < 3). Having previously undergone BTI. The last injection must have been performed at least 4 months prior to inclusion. Affiliation to the French social security regime or a similar regime. Patient (or the legal guardian if under guardian adult patient) has signed the informed consent form.", "candidate_expression": "((< 3) AND (Adult patient under guardianship with consent obtained and the legal guardian's authorisation obtained) AND (BDAE) AND (BTI) AND (Boston Diagnostic Aphasia Examination) AND (Capable of understanding instructions and participating in the definition of a therapeutic goal) AND (Patient (or the legal guardian if under guardian adult patient) has signed the informed consent form) AND (Single) AND (TIA) AND (aged) AND (at least 4 months prior to inclusion) AND (between 18 to 75 years) AND (inclusion) AND (injection) AND (more than 6 months) AND (stroke) AND ((Males) OR (females)))"}
```
