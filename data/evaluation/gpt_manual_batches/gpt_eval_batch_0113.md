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
{"candidate_id": "LLM02801", "doc_id": "NCT02886962_inc", "case_bucket": "or", "source_criterion": "Adult patients (= 18 years) Patient on hemodialysis treatment for at least 1 month Patient with a history of, or presenting a new episode of atrial fibrillation (either permanent or paroxysmal). Patient with a CHADS2VASC score =2 Patient with high risk of bleeding as defined by (1) HASBLED score =3 OR (2) HASBLED = CHADS2VASC score, OR (3) recent history of severe bleeding (type 3a, 3b, 3c), particularly cerebral or gastrointestinal, OR (4) prior recurrent (>2) history of falls. Patient capable of understanding information about the study and of giving his/her consent Patient informed of the preliminary medical exam results Patient with healthcare insurance Written consent signed", "candidate_expression": "((Adult) AND (CHADS2VASC score) AND (CHADS2VASC score =2) AND (HASBLED score =3) AND (Patient capable of understanding information about the study and of giving his/her consent) AND (Patient informed of the preliminary medical exam results) AND (Written consent signed) AND (atrial fibrillation new episode) AND (falls recurrent >2) AND (hemodialysis at least 1 month) AND (risk of bleeding high) AND (severe bleeding type 3a, 3b, 3c cerebral gastrointestinal) AND (years = 18))"}
{"candidate_id": "LLM02802", "doc_id": "NCT02721017_inc", "case_bucket": "other", "source_criterion": "scheduled for Nuss procedure for pectus excavatum correction at least 13 years old at the time of the procedure", "candidate_expression": "((Nuss procedure scheduled) AND (old at least 13 years at the time of the procedure) AND (pectus excavatum))"}
{"candidate_id": "LLM02803", "doc_id": "NCT02650388_exc", "case_bucket": "other", "source_criterion": "Died before TAVI Not willing to participate", "candidate_expression": "((Died before TAVI) AND (Not willing to participate))"}
{"candidate_id": "LLM02804", "doc_id": "NCT02348918_exc", "case_bucket": "or", "source_criterion": "Active proliferative diabetic retinopathy (PDR) in the study eye such as NVE, NVD, vitreous hemorrhage, or neovascular glaucoma. Uncontrolled hypertension defined as systolic >180 mmHg or > 160 mmHg on 2 consecutive measurements or diastolic > 100 mmHg on optimal medical regimen Screening HgA1c blood test > 10.0 Focal laser photocoagulation or intravitreal/periocular steroids of any type in the study eye within the last 90 days prior to study enrollment. A history of intravitreal anti-VEGF injection of any type in the study eye within the last 45 days prior to study enrollment. History of rhegmatogenous retinal detachment, retinal tear(s), or traction retinal detachments in the study eye. Epiretinal membrane and/or vitreomacular traction in the study eye as determined by the central reading center. Previous pars plana vitrectomy in the study eye Any intraocular surgery in the study eye within the last 90 days prior to study enrollment. YAG laser treatment in the study eye in last 30 days prior to study enrollment. High myopia in the study eye, with a spherical equivalent of >8.00D at screening Other ocular pathologies that in the investigator's opinion would interfere with the subject's vision in the study eye. Chronic or recurrent uveitis. Ongoing ocular infection or inflammation in either eye. A history of cataract surgery complications/vitreous loss in the study eye. Congenital eye malformations in the study eye. A history of penetrating ocular trauma in the study eye. Mentally handicapped. Pregnant female, as determined for women less than 60 years old by a positive urine pregnancy test during the screening window. Nursing female. Currently participating in any other clinical research study. Contraindication to the study medication.", "candidate_expression": "((> 10.0) AND (> 100 mmHg) AND (>8.00D) AND (Active proliferative diabetic retinopathy (PDR)) AND (Congenital eye malformations) AND (Contraindication) AND (Currently participating in any other clinical research study.) AND (HgA1c blood test) AND (High myopia) AND (History of) AND (Mentally handicapped) AND (Nursing) AND (Ongoing) AND (Other) AND (Pregnant) AND (Previous) AND (Screening) AND (Uncontrolled hypertension) AND (YAG laser treatment) AND (anti-VEGF injection) AND (at screening) AND (cataract surgery) AND (during the screening window) AND (female) AND (history of) AND (in either eye) AND (in last 30 days prior to study enrollment) AND (in the study eye) AND (intraocular surgery) AND (intravitreal) AND (less than 60 years) AND (ocular pathologies) AND (old) AND (on 2 consecutive measurements) AND (on optimal medical regimen) AND (optimal medical regimen) AND (pars plana vitrectomy) AND (penetrating ocular trauma) AND (positive) AND (spherical equivalent) AND (study enrollment) AND (study medication) AND (urine pregnancy test) AND (uveitis) AND (within the last 45 days prior to study enrollment) AND (within the last 90 days prior to study enrollment) AND (women) AND (would interfere with the subject's vision in the study eye) AND ((> 160 mmHg) OR (>180 mmHg)) AND ((diastolic) OR (systolic)) AND ((Focal laser photocoagulation) OR (intravitreal/periocular steroids)) AND ((retinal tear(s)) OR (rhegmatogenous retinal detachment) OR (traction retinal detachments)) AND ((NVD) OR (NVE) OR (neovascular glaucoma) OR (vitreous hemorrhage)) AND ((Epiretinal membrane traction) OR (vitreomacular traction)) AND ((Chronic) OR (recurrent)) AND ((ocular infection) OR (ocular inflammation)) AND ((cataract surgery complications) OR (vitreous loss)))"}
{"candidate_id": "LLM02805", "doc_id": "NCT03016741_exc", "case_bucket": "or", "source_criterion": "Prior treatment with enzalutamide or abiraterone acetate for > 14 days prior to enrollment and completion of baseline tests. Receipt of chemotherapy for prostate or other cancer within the past 12 months with residual cognitive deficits, or receipt of chemotherapy for mCRPC. Patients/physicians planning treatment with chemotherapy during the 12 month period of the investigation are also ineligible. History of cognitive impairment or dysfunction, including a history of dementia, Alzheimer's disease, stroke with residual cognitive deficits, cognitive dysfunction related to alcohol or substance abuse, or cognitive dysfunction related to prior treatment for any cancer. Patients with a seizure history, history of recurrent falls, or known brain metastases are excluded from this clinical trial because of their poor prognosis and because of their heightened risk of seizure or progressive cognitive and/or neurologic dysfunction that would confound the evaluation. Uncontrolled intercurrent illness including, but not limited to, uncontrolled diabetes, ongoing or active infection, symptomatic congestive heart failure (New York Heart Association Class III and IV heart failure), unstable angina pectoris, cardiac arrhythmia, or psychiatric illness/social situations/substance abuse that would limit compliance with study requirements. Patients with a \"currently active\" second malignancy other than non-melanoma skin cancers are not eligible. Patients are not considered to have a \"currently active\" malignancy if they have completed all therapy and are now considered without evidence of disease for 1 year. Patients with cognitive dysfunction related to treatment of another malignancy, including a history of \"chemo-brain\", are ineligible. Patients taking psychotropic medications or illicit drugs that may alter cognition, concentration, or behavior. Appropriate treatment by a licensed provider with medications for depression or anxiety, including but not limited to SSRIs, SNRIs, and standard dose benzodiazepines at a stable dose, is permitted", "candidate_expression": "((Class III and IV) AND (New York Heart Association) AND (Uncontrolled) AND (another) AND (any) AND (cancer) AND (congestive heart failure) AND (currently active) AND (enrollment) AND (for > 14 days) AND (heart failure) AND (history) AND (history of) AND (intercurrent illness) AND (mCRPC) AND (malignancy) AND (non-melanoma skin cancers) AND (other) AND (other than) AND (prior) AND (prior to enrollment) AND (residual cognitive deficits) AND (second) AND (symptomatic) AND (treatment) AND (uncontrolled) AND (within the past 12 months) AND ((cancer) OR (prostate cancer)) AND ((cognitive dysfunction) OR (cognitive impairment)) AND ((abiraterone acetate) OR (enzalutamide)) AND ((Alzheimer's disease) OR (alcohol abuse) OR (cognitive dysfunction) OR (dementia) OR (stroke) OR (substance abuse)) AND ((brain metastases) OR (recurrent falls) OR (seizure)) AND ((active) OR (ongoing)) AND ((cardiac arrhythmia) OR (diabetes) OR (infection) OR (psychiatric illness) OR (social situations) OR (substance abuse) OR (unstable angina pectoris)) AND ((cognitive dysfunction) OR (malignancy)) AND ((illicit drugs) OR (psychotropic medications)) AND ((alter behavior) OR (alter cognition) OR (alter concentration)) AND ((chemotherapy)))"}
{"candidate_id": "LLM02806", "doc_id": "NCT02312089_inc", "case_bucket": "scope", "source_criterion": "Women subjected to ICSI through controlled ovarian hyperstimulation (COH) with pituitary downregulation by GnRH antagonist.", "candidate_expression": "((COH) AND (GnRH antagonist) AND (ICSI) AND (Women) AND (ovarian hyperstimulation) AND (pituitary downregulation))"}
{"candidate_id": "LLM02807", "doc_id": "NCT02431559_exc", "case_bucket": "or", "source_criterion": "1. Prior exposure to doxorubicin, PLD or any other anthracycline, motolimod and other TLR agonists, MEDI4736 or checkpoint inhibitors, such as anti-CTLA4 and anti-PD1/anti-PD-L1 antibodies. 2. Subjects with platinum-refractory disease, defined as disease progression while receiving first line platinum-based therapy. 3. Clinically significant persistent immune-related adverse events following prior therapy. 4. Subjects with history or evidence upon physical examination of CNS disease, including primary brain tumor, seizures not controlled with standard medical therapy, any brain metastases, or, within six months prior to Day 1 of this study, history of cerebrovascular accident (CVA, stroke), transient ischemic attack (TIA) or subarachnoid hemorrhage. 5. Subjects with clinically significant cardiovascular disease. This includes: 1. Resisted hypertension 2. Myocardial infarction or unstable angina within 6 months prior to Day 1 of the study. 3. History of serious ventricular arrhythmia (i.e., ventricular tachycardia or ventricular fibrillation) or cardiac arrhythmias requiring anti-arrhythmic medications, except for atrial fibrillation that is well controlled with anti-arrhythmic medication. 4. Baseline ejection fraction ≤ 50% as assessed by echocardiogram or MUGA. 5. New York Heart Association (NYHA) Class II or higher congestive heart failure. 6. Grade 2 or higher peripheral ischemia, except for brief (< 24 hrs) episodes of ischemia managed non-surgically and without permanent deficit. 6. History of pneumonitis or interstitial lung disease. 7. Active, suspected or prior documented autoimmune disease (including inflammatory bowel disease, celiac disease, Wegner's granulomatosis, active Hashimoto's thyroiditis, rheumatoid arthritis, lupus, scleroderma and its variants, multiple sclerosis, myasthenia gravis). Vitiligo, type I diabetes mellitus, residual hypothyroidism due to autoimmune condition only requiring hormone replacement, psoriasis not requiring systemic treatment, or conditions not expected to recur in the absence of an external trigger are permitted. 8. Other malignancy within 2 years prior to Day 1 of the study, except for those treated with surgical intervention only. 9. Subjects with clinical symptoms or signs of gastrointestinal obstruction and/or who require drainage gastrostomy tube and/or parenteral hydration or nutrition. 10. Known immunodeficiency or HIV, Hepatitis B or Hepatitis C positivity. 11. History of severe allergic reactions to any unknown allergens or components of the study drugs. 12. Other serious illnesses (e.g., serious infections requiring antibiotics, bleeding disorders). 13. Prior treatment in any other interventional clinical trial within 4 weeks prior to Day 1 of the study. 14. Mental impairment that may compromise compliance with the requirements of the study. 15. Lack of availability for immunological and clinical follow-up assessment. 16. Women who are breastfeeding or pregnant as evidenced by positive serum pregnancy test 17. Subjects unwilling to use acceptable methods of contraception. -Female subjects should refrain from breastfeeding throughout this period. 18. Any condition that, in the clinical judgment of the treating physician, is likely to prevent the subject from complying with any aspect of the protocol or that may put the subject at unacceptable risk. 19. Subjects must not donate blood while on study and for at least 90 days following the last MEDI4736 treatment. 20. History of allogeneic organ transplant", "candidate_expression": "((2 or higher) AND (< 24 hrs) AND (Baseline) AND (CNS disease) AND (CVA) AND (Class II or higher) AND (Clinically significant) AND (Day 1 of the study) AND (Day 1 of this study) AND (Female) AND (Grade 2 or higher) AND (HIV) AND (Hashimoto's thyroiditis) AND (Hepatitis B) AND (Hepatitis C) AND (History) AND (Lack of) AND (MEDI4736) AND (MUGA) AND (Mental impairment) AND (Myocardial infarction) AND (New York Heart Association (NYHA)) AND (PLD) AND (Prior) AND (Resisted hypertension) AND (TLR agonists) AND (Vitiligo) AND (Wegner's granulomatosis) AND (Women) AND (acceptable) AND (allergic reactions) AND (allogeneic organ transplant) AND (anthracycline) AND (anti-CTLA4) AND (anti-PD-L1 antibodies) AND (anti-PD1 antibodies) AND (anti-arrhythmic medication) AND (anti-arrhythmic medications) AND (atrial fibrillation) AND (autoimmune condition) AND (autoimmune disease) AND (availability for) AND (bleeding disorders) AND (brain metastases) AND (breastfeeding) AND (brief) AND (cardiac arrhythmias) AND (cardiovascular disease) AND (celiac disease) AND (cerebrovascular accident) AND (checkpoint inhibitors) AND (clinical follow-up assessment) AND (clinical symptoms of gastrointestinal obstruction) AND (clinically significant) AND (compromise compliance) AND (conditions) AND (congestive heart failure) AND (contraception) AND (controlled) AND (disease progression) AND (donate blood) AND (doxorubicin) AND (drainage gastrostomy tube) AND (due to autoimmune condition) AND (echocardiogram) AND (ejection fraction) AND (except) AND (except for) AND (first line platinum-based therapy) AND (following prior therapy) AND (for at least 90 days following the last MEDI4736 treatment) AND (hormone replacement) AND (illnesses) AND (immune-related adverse events) AND (immunodeficiency) AND (immunological follow-up assessment) AND (infections requiring antibiotics) AND (inflammatory bowel disease) AND (interstitial lung disease) AND (ischemia) AND (lupus) AND (malignancy) AND (motolimod) AND (multiple sclerosis) AND (myasthenia gravis) AND (non) AND (not) AND (not expected to recur) AND (on study) AND (parenteral hydration) AND (parenteral nutrition) AND (peripheral ischemia) AND (permanent deficit) AND (persistent) AND (platinum-refractory disease) AND (pneumonitis) AND (positive) AND (pregnant) AND (primary brain tumor) AND (prior therapy) AND (psoriasis) AND (refrain from) AND (requiring anti-arrhythmic medications) AND (requiring hormone replacement) AND (requiring systemic treatment) AND (residual hypothyroidism) AND (rheumatoid arthritis) AND (scleroderma) AND (scleroderma variants) AND (seizures) AND (serious) AND (serum pregnancy test) AND (severe) AND (signs of gastrointestinal obstruction) AND (standard medical therapy) AND (stroke) AND (subarachnoid hemorrhage) AND (surgical intervention) AND (surgically) AND (systemic treatment) AND (the last MEDI4736 treatment) AND (this period) AND (those) AND (throughout this period.) AND (to any unknown allergens or components of the study drugs) AND (transient ischemic attack (TIA)) AND (treatment) AND (type I diabetes mellitus) AND (unstable angina) AND (unwilling) AND (ventricular arrhythmia) AND (ventricular fibrillation) AND (ventricular tachycardia) AND (well controlled with anti-arrhythmic medication) AND (while on study) AND (while receiving first line platinum-based therapy) AND (within 2 years prior to Day 1 of the study) AND (within 6 months prior to Day 1 of the study) AND (within six months prior to Day 1 of this study) AND (without) AND (≤ 50%))"}
{"candidate_id": "LLM02808", "doc_id": "NCT00440245_exc", "case_bucket": "or", "source_criterion": "asthma and COPD", "candidate_expression": "((COPD) OR (asthma))"}
{"candidate_id": "LLM02809", "doc_id": "NCT02827487_inc", "case_bucket": "or", "source_criterion": "Women with expected difficult IUD insertion like nulliparous women and women with previous cesarean section.", "candidate_expression": "((IUD insertion) AND (Women) AND (cesarean section) AND (difficult) AND (expected) AND (nulliparous) AND (previous) AND (women))"}
{"candidate_id": "LLM02810", "doc_id": "NCT02579928_exc", "case_bucket": "or", "source_criterion": "Current inpatient hospitalization or active suicidal ideation requiring referral for inpatient hospitalization for safety. History of psychotic disorder or manic episode diagnosed by MINI-KID History of substance dependence diagnosis by MINI-KID (excluding tobacco) or positive urine toxicology. Pregnancy (urine pregnancy tests on the day of scans for menstruating girls). Inability to provide written informed consent according to the Yale Human Investigation Committee (HIC) guidelines in English.", "candidate_expression": "((MINI-KID) AND (Pregnancy) AND (inpatient) AND (inpatient hospitalization) AND (menstruating girls) AND (referral requiring) AND (urine pregnancy tests on the day of scans) AND NOT (tobacco) AND NOT (written informed consent Yale Human Investigation Committee (HIC) guidelines) AND ((manic episode) OR (psychotic disorder)) AND ((substance dependence) OR (urine toxicology positive)) AND ((hospitalization Current) OR (suicidal ideation active)))"}
{"candidate_id": "LLM02811", "doc_id": "NCT01205334_exc", "case_bucket": "or", "source_criterion": "Severe intercurrent infection Known HIV positivity Pregnant or lactating History of hypersensitivity reactions to murine protein-containing products.", "candidate_expression": "((HIV positivity) AND (hypersensitivity reactions) AND (infection Severe intercurrent) AND (murine) AND (murine protein-containing products) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM02812", "doc_id": "NCT00440245_inc", "case_bucket": "or", "source_criterion": "asthma or COPD", "candidate_expression": "((COPD) OR (asthma))"}
{"candidate_id": "LLM02813", "doc_id": "NCT03338296_inc", "case_bucket": "or", "source_criterion": "Healthy male or female adolescents, age 12 to 17 years (inclusive) at Screening, with a body mass index (BMI) that is greater than or equal to the United States-weighted mean of the 95th percentile based on age and sex with a body weight greater than 60 kilograms (kg). Participants with Type 2 diabetes mellitus (T2DM) may have a pre-existing or new diagnosis of T2DM. HbA1c =6.5% fasting plasma glucose (FPG) =126 mg/dL (7.0 mmol/L) Participants and their families not planning to move away from the area for the duration of the study Participants able and willing to comply with all aspects of the study, including a standardized, reduced calorie diet and an age appropriate, increased physical activity program Participants considered in stable health in the opinion of the investigator Able and willing to support and supervise study participation in the opinion of the investigator, including consideration of any existing physical, medical, or mental condition that prevents compliance with the protocol Able and willing to personally comply with and execute all aspects of the study requirements for the caregivers or guardians", "candidate_expression": "((Able to personally comply) AND (HbA1c =6.5%) AND (Healthy) AND (able to comply) AND (adolescents) AND (age 12 to 17 years at Screening) AND (body mass index (BMI) greater than or equal to the United States-weighted mean of the 95th percentile greater than or equal to the 95th percentile) AND (body weight greater than 60 kilograms (kg) based on age based on sex) AND (caregivers) AND (fasting plasma glucose (FPG) =126 mg/dL 7.0 mmol/L) AND (female) AND (guardians) AND (increased physical activity program age appropriate) AND (male) AND (reduced calorie diet standardized) AND (stable health) AND (willing to comply) AND (willing to personally comply) AND NOT (planning to move away for the duration of the study))"}
{"candidate_id": "LLM02814", "doc_id": "NCT03115151_inc", "case_bucket": "other", "source_criterion": "Adult subjects aged 18 years or older Scheduled for elective posterior lumbar spinal fusion surgery between 1 and 3 levels", "candidate_expression": "((18 years or older) AND (Adult) AND (Scheduled for) AND (aged) AND (between 1 and 3 levels) AND (elective) AND (posterior lumbar spinal fusion surgery))"}
{"candidate_id": "LLM02815", "doc_id": "NCT03234816_exc", "case_bucket": "other", "source_criterion": "Cardiac morbidities Hypertensive disorders of pregnancy, Peripartum bleeding Baseline systolic blood pressure (SBP) < 100 mmHg Body mass index > 35", "candidate_expression": "((Body mass index > 35) AND (Cardiac morbidities) AND (Hypertensive disorders of pregnancy) AND (Peripartum bleeding) AND (SBP) AND (systolic blood pressure Baseline < 100 mmHg))"}
{"candidate_id": "LLM02816", "doc_id": "NCT00279552_exc", "case_bucket": "or", "source_criterion": "Patients who were pregnant, nursing or not able to give written informed consent were excluded.", "candidate_expression": "((nursing able to give written informed consent) AND (pregnant))"}
{"candidate_id": "LLM02817", "doc_id": "NCT02490839_exc", "case_bucket": "or", "source_criterion": "pregnant or nursing woman serious concomitant illness and malignant tumor of any kind history of hypersensitivity to test drugs serious bleeding during the course of the ulcer previous gastric surgery receiving bismuth salts, PPIs, or antibiotics in the previous month.", "candidate_expression": "((PPIs) AND (antibiotics) AND (bismuth salts) AND (bleeding serious during the course of the ulcer) AND (gastric surgery previous) AND (hypersensitivity history) AND (illness serious concomitant) AND (malignant tumor any kind) AND (nursing) AND (pregnant) AND (test drugs) AND (ulcer) AND (woman))"}
{"candidate_id": "LLM02818", "doc_id": "NCT02595190_inc", "case_bucket": "or", "source_criterion": "1. Diagnosed with symptomatic sacral perineurial cysts(e.g., lumbosacral or perineal pain, fecal or urinary functions change, sexual function change, lower limb radiation pain, muscle abate, paresthesia, etc) 2. Visual analog scale more than or equal to 4 3. Signed the informed consent 4. Years, range 18-60 5. Self-rating anxiety scale (SAS) and self-rating depression scale (SDS) scores < 50 6. No Congenital,Mental and other Nervous system diseases 7. No Serious Cardiac,Pulmonary,Hepatic and Nephritic disease 8. No history of drug allergy 9. No pain(including dysmenorrhea) or drug use (e.g., antipyretics,sleeping pills) within the last month 10. MRI finding of sacral perineurial cysts, but without any clinical symptoms, included in the negative control group 11. MRI finding healthy volunteers don't have sacral perineurial cysts, included in the negative control groupblank control group", "candidate_expression": "((Congenital diseases) AND (MRI finding healthy volunteers don't have sacral perineurial cysts, included in the negative control groupblank control group) AND (Mental disease) AND (Nervous system diseases) AND (SAS) AND (SDS) AND (Self-rating anxiety scale) AND (Signed the informed consent) AND (Visual analog scale more than or equal to 4) AND (Years 18-60) AND (allergy) AND (dysmenorrhea) AND (sacral perineurial cysts( symptomatic) AND (self-rating depression scale) AND NOT (drug) AND NOT (Cardiac,Pulmonary,Hepatic) AND ((Cardiac) OR (Hepatic) OR (Nephritic disease) OR (Pulmonary)) AND ((drug last month) OR NOT (pain)) AND ((functions change, fecal) OR (lower limb radiation pain) OR (lumbosacral pain) OR (muscle abate) OR (paresthesia) OR (perineal pain) OR (sexual function change) OR (urinary functions change)))"}
{"candidate_id": "LLM02819", "doc_id": "NCT03476850_exc", "case_bucket": "or", "source_criterion": "Chronic pain or narcotic usage during the preceding 30 days Infection at or near the intended needle insertion site Complex or altered abdominal wall anatomy Weight <45kg", "candidate_expression": "((<45kg) AND (Chronic pain) AND (Complex abdominal wall anatomy) AND (Infection) AND (Weight) AND (altered abdominal wall anatomy) AND (during the preceding 30 days) AND (intended needle insertion site) AND (narcotic))"}
{"candidate_id": "LLM02820", "doc_id": "NCT01994382_exc", "case_bucket": "or", "source_criterion": "Richter's syndrome, Burkitt's lymphoma, or Burkitt-like Lymphoma (transformed DLBCL from Follicular NHL are eligible). Prior transplant with stem cell infusion 90 days or active graft-versus-host treatment within 8 weeks of Day 1. Prior therapy with SYK inhibitors. Chronic treatment with strong CYP3A4 inhibitor/ inducer, acid reducing agent, Proton pump inhibitors Known lymphomatous involvement of the CNS. Persistent, unresolved NCI CTCAE v4.0 ≥ Grade 2, previous drug-related toxicity (except alopecia, erectile impotence, hot flashes, libido, neuropathy). Prior monoclonal antibody, radioimmunoconjugate, antibody drug conjugate, phototherapy, radiotherapy, chemotherapy, immunotherapy, immunosuppressive therapy, or any test agent within 3 weeks or for alemtuzumab 8 weeks of Day 1. For CTCL: (TSEBT) within 12 weeks, or initiation of topical steroid, nitrogen mustard, or topical retinoid within 2 weeks. (Stable topical ≥ 4 weeks prior to Day 1 allowed). Known carrier or infection for HIV/Hep B or C. HCV ab+ must be PCR-. HBV ab+ must be HBsAg- or undetectable DNA Active infection requiring systemic treatment, Significant GI disease, previous major gastric/bowel surgery, difficulty swallowing or malabsorption syndrome. Major surgery within 4 weeks Previous malignancies within 2 yrs. unless relapse risk is small (< 5%). Current use of systemic steroids >20 mg QD prednisone (or equivalent) Breastfeeding or pregnant (intention to become) females or participation in other clinical trials", "candidate_expression": "((8 weeks of Day 1) AND (90 days of Day 1) AND (>20 mg QD) AND (Breastfeeding) AND (Burkitt's lymphoma) AND (Burkitt-like Lymphoma) AND (CTCL) AND (DLBCL) AND (Day 1) AND (Follicular NHL) AND (GI disease) AND (HBV ab+) AND (HBsAg-) AND (HCV ab+) AND (Hep B infection for) AND (Hep C infection for) AND (Major) AND (NCI CTCAE v4.0) AND (PCR-) AND (Prior) AND (Proton pump inhibitors) AND (Richter's syndrome) AND (SYK inhibitors) AND (Significant) AND (TSEBT) AND (acid reducing agent) AND (active) AND (alemtuzumab) AND (alopecia) AND (antibody drug conjugate) AND (bowel surgery) AND (chemotherapy) AND (difficulty swallowing) AND (drug-related toxicity) AND (erectile impotence) AND (except) AND (females) AND (gastric surgery) AND (graft-versus-host treatment) AND (hot flashes) AND (immunosuppressive therapy) AND (immunotherapy) AND (infection) AND (infection for HIV) AND (initiation) AND (libido) AND (lymphomatous involvement of the CNS) AND (major) AND (malabsorption syndrome) AND (malignancies) AND (monoclonal antibody) AND (neuropathy) AND (nitrogen mustard) AND (phototherapy) AND (prednisone) AND (pregnant) AND (previous) AND (radioimmunoconjugate) AND (radiotherapy) AND (requiring systemic treatment) AND (stem cell infusion) AND (strong CYP3A4 inducer) AND (strong CYP3A4 inhibitor) AND (surgery) AND (systemic steroids) AND (systemic treatment) AND (therapy) AND (topical retinoid) AND (topical steroid) AND (transplant) AND (undetectable DNA) AND (unless relapse risk is small (< 5%)) AND (within 12 weeks) AND (within 2 weeks) AND (within 2 yrs.) AND (within 3 weeks of Day 1) AND (within 4 weeks) AND (within 8 weeks of Day 1) AND (≥ 4 weeks prior to Day 1) AND (≥ Grade 2))"}
{"candidate_id": "LLM02821", "doc_id": "NCT02995291_exc", "case_bucket": "or", "source_criterion": "contra-indications for regular dental treatment medical history that contraindicates the use of epinephrine participant taken an opioid or an opioid like analgesic within 24 hours pregnant", "candidate_expression": "((contra-indications) AND (contraindicates medical history) AND (epinephrine) AND (pregnant) AND (regular dental treatment) AND ((opioid) OR (opioid like analgesic)))"}
{"candidate_id": "LLM02822", "doc_id": "NCT02604459_inc", "case_bucket": "other", "source_criterion": "Subject or legal representative has voluntarily signed the informed consent approved by the Institutional Review Board, Hip fracture surgery scheduled under general anesthesia Subject is 65 years or older on the day of surgery", "candidate_expression": "((Hip fracture surgery) AND (Subject or legal representative has voluntarily signed the informed consent approved by the Institutional Review Board,) AND (general anesthesia) AND (older 65 years or older) AND (surgery))"}
{"candidate_id": "LLM02823", "doc_id": "NCT02535299_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes mellitus,presence of autoimmune diabetes indicated by antibodies to insulin, islet cells, and GAD; Gestational diabetes; patients with heart, liver, or renal function impairment;presence of severe infections or cerebrovascular disease;", "candidate_expression": "((GAD) AND (Gestational diabetes) AND (Type 1 diabetes mellitus) AND (antibodies) AND (autoimmune diabetes) AND (cerebrovascular disease) AND (heart function impairment) AND (infections) AND (insulin) AND (islet cells) AND (liver function impairment) AND (renal function impairment) AND (severe))"}
{"candidate_id": "LLM02824", "doc_id": "NCT02974660_inc", "case_bucket": "other", "source_criterion": "patients who underwent successful TAVI with any approved TAVI device via transfemoral access with use of any of the approved vascular closure devices provided written informed consent", "candidate_expression": "((TAVI) AND (TAVI device) AND (provided written informed consent) AND (successful) AND (transfemoral access) AND (vascular closure devices))"}
{"candidate_id": "LLM02825", "doc_id": "NCT02413970_exc", "case_bucket": "or", "source_criterion": "Central + mixed apneas > 25% of the total apnea-hypopnea index (AHI) Any anatomical finding that would compromise the performance of upper airway stimulation, such as the presence of complete concentric collapse of the soft palate Any condition or procedure that has compromised neurological control of the upper airway Patients who are unable or do not have the necessary assistance to operate the patient remote Patients who are pregnant or plan to become pregnant Patients who will require magnetic resonance imaging (MRI) Patients with an implantable device that may be susceptible to unintended interaction with the Inspire system. Body Mass Index (BMI) of > 32 Any chronic medical illness or condition that contraindicates a surgical procedure under general anesthesia, as judged by the clinical study Investigator Has a terminal illness with life expectancy < 12 months Active psychiatric disease (psychotic illness, major depression, or acute anxiety attacks) which prevents subject compliance with the requirements of the investigational study testing Any other reason the investigator deems subject is unfit for participation in the study", "candidate_expression": "((AHI) AND (BMI > 32) AND (Body Mass Index) AND (Central apneas) AND (MRI) AND (Patients who are pregnant or plan to become pregnant) AND (acute anxiety attacks) AND (contraindicates) AND (general anesthesia) AND (life expectancy < 12 months) AND (magnetic resonance imaging) AND (major depression) AND (mixed apneas) AND (psychiatric disease) AND (psychotic illness) AND (surgical procedure) AND (total apnea-hypopnea index > 25%))"}
```
