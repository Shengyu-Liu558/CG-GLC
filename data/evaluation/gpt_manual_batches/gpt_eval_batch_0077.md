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
{"candidate_id": "LLM01901", "doc_id": "NCT02385448_inc", "case_bucket": "or", "source_criterion": "Good general health Older than the age of legal consent (i.e. 18 years old) Sonographic diagnosis of ovarian endometrioma with diameter at least 4cm on 2 separate scans at least 6 weeks apart No contraindication to use of progesterone or combined oral contraceptive pills Not attempting to conceive either at the time of study entry or for at least 2 years after surgery Willing and able to participate after the study has been explained", "candidate_expression": "((Good general health) AND (Sonographic 2 separate scans) AND (age Older than the age of legal consent 18 years old) AND (conceive attempting) AND (ovarian endometrioma diameter at least 4cm) AND NOT (contraindication) AND ((combined oral contraceptive pills) OR (progesterone)) AND ((at the time of study entry) OR (for at least 2 years after surgery)))"}
{"candidate_id": "LLM01902", "doc_id": "NCT01490034_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01903", "doc_id": "NCT03363295_inc", "case_bucket": "other", "source_criterion": "Any patients that will be submitted to phacoemulsification surgery in the Hospital de Clinicas of State University of Campinas (BRAZIL) Patients over 18 years old Patients who are able to perform SD-OCT Patients who sign the consent form", "candidate_expression": "((Hospital de Clinicas of State University of Campinas (BRAZIL)) AND (Patients who sign the consent form) AND (SD-OCT able to perform) AND (old over 18 years) AND (phacoemulsification surgery will be submitted to))"}
{"candidate_id": "LLM01904", "doc_id": "NCT02511574_inc", "case_bucket": "other", "source_criterion": "gestational age between 20 weeks and 23 weeks and 6 days singleton pregnancies", "candidate_expression": "((between 20 weeks and 23 weeks and 6 days) AND (gestational age) AND (singleton pregnancies))"}
{"candidate_id": "LLM01905", "doc_id": "NCT02739295_inc", "case_bucket": "other", "source_criterion": "Toxic epidermal necrolysis with SCORTEN 1 to 5 at admission", "candidate_expression": "((1 to 5) AND (SCORTEN) AND (Toxic epidermal necrolysis) AND (admission) AND (at admission))"}
{"candidate_id": "LLM01906", "doc_id": "NCT02609698_exc", "case_bucket": "or", "source_criterion": "Patients with any contraindications or hypersensitivity related to antiplatelet therapy Patients with Acute Myocardial Infarction (ST elevation myocardial infarction, Non ST elevation myocardial infarction) Patients who are anticipated to receive treatment or surgery that may require desisting the administration of antiplatelet therapy for 2 weeks or longer during the period of the clinical trial Chronic total occlusion (CTO) lesions, in-stent restenosis (ISR) Patients experiencing cardiogenic shock Women who are breastfeeding, pregnant, or desiring pregnancy Patients with findings of hemorrhage Patients with a life expectancy of less than 1 year Patients who have received a drug-eluting stent (DES) procedure within the past 6 months Any other patients judged by the investigator to be unsuitable for the trial", "candidate_expression": "((Acute Myocardial Infarction) AND (CTO) AND (Chronic total occlusion) AND (DES) AND (ISR) AND (Non ST elevation myocardial infarction) AND (ST elevation myocardial infarction) AND (Women who are breastfeeding, pregnant, or desiring pregnancy) AND (anticipated to) AND (antiplatelet therapy) AND (cardiogenic shock) AND (contraindications) AND (drug-eluting stent procedure) AND (for 2 weeks or longer) AND (hemorrhage) AND (hypersensitivity) AND (in-stent restenosis) AND (less than 1 year) AND (life expectancy) AND (past 6 months) AND (surgery) AND (treatment))"}
{"candidate_id": "LLM01907", "doc_id": "NCT02686021_inc", "case_bucket": "scope", "source_criterion": "planned sequential both-sided lower third molar extraction (split-mouth) with osteotomy (with or without upper molar extraction in local anesthesia) able to understand the study and the NRS scale", "candidate_expression": "((able to understand the study) AND (local anesthesia) AND (lower third molar extraction planned sequential both-sided split-mouth) AND (osteotomy) AND (upper molar extraction))"}
{"candidate_id": "LLM01908", "doc_id": "NCT01959425_exc", "case_bucket": "or", "source_criterion": "OAT required for reasons not related to AF (i.e., prosthetic valve, PV stenosis, previous pulmonary embolism, presence of spontaneous echo contrast [SEC] at standard echo performed at 3-months follow-up). Any cardiac surgery within the past 60 days (2 months) or valvular cardiac surgical procedure at any time (i.e., ventriculotomy, atriotomy, and valve repair or replacement and presence of a prosthetic valve) Previous myocardial infarction (MI) or a percutaneous coronary intervention PCI within the past 3 months Awaiting cardiac transplantation or other cardiac surgery within the next 365 days (12 months) Documented left atrial thrombus Significant pulmonary disease, (e.g., restrictive pulmonary disease, constrictive or COPD) or any other disease or malfunction of the lungs or respiratory system that produces chronic symptoms Significant medical problem that in the opinion of the investigator would preclude enrollment in this study Women who are pregnant (as evidenced by pregnancy test if pre-menopausal) Acute illness or active systemic infection or sepsis Unstable angina Contraindication to anticoagulation (i.e., heparin, warfarin or another commercially available anticoagulation medication) History of blood clotting or bleeding abnormalities Life expectancy less than 360 days (12 months) Uncontrolled Heart Failure or NYHA Class III or IV heart failure Enrollment in a clinical study evaluating another device or drug, within the past 6 months Unable or unwilling to comply with protocol requirements", "candidate_expression": "((2 months) AND (3-months follow-up) AND (AF) AND (Awaiting) AND (Contraindication) AND (Enrollment in a clinical study evaluating another device or drug, within the past 6 months) AND (Life expectancy) AND (MI) AND (OAT) AND (PCI) AND (SEC) AND (Significant) AND (Unable or unwilling to comply with protocol requirements) AND (Uncontrolled) AND (Unstable angina) AND (Women who are pregnant (as evidenced by pregnancy test if pre-menopausal)) AND (anticoagulation) AND (follow-up) AND (left atrial thrombus) AND (less than 12 months) AND (less than 360 days) AND (not) AND (pulmonary disease) AND (spontaneous echo contrast) AND (within 12 months) AND (within the next 365 days) AND (within the past 3 months) AND (within the past 60 days) AND ((cardiac surgery) OR (valvular cardiac surgical)) AND ((atriotomy) OR (prosthetic valve)) OR (valve repair) OR (valve replacement) OR (ventriculotomy)) AND ((myocardial infarction) OR (percutaneous coronary intervention)) AND ((cardiac surgery) OR (cardiac transplantation)) AND ((COPD) OR (restrictive pulmonary disease)) AND ((sepsis) OR (systemic infection)) AND ((PV stenosis) OR (prosthetic valve) OR (pulmonary embolism) OR (standard echo)) AND ((heparin) OR (warfarin)) AND ((bleeding abnormalities) OR (blood clotting abnormalities)) AND ((Heart Failure) OR (heart failure)) AND ((NYHA Class III) OR (NYHA Class IV)))"}
{"candidate_id": "LLM01909", "doc_id": "NCT02995291_inc", "case_bucket": "other", "source_criterion": "18 years of age or older capable of providing informed consent", "candidate_expression": "((18 years of or older) AND (age) AND (capable of providing informed consent))"}
{"candidate_id": "LLM01910", "doc_id": "NCT02985242_inc", "case_bucket": "or", "source_criterion": "women and men between 18 - 80 years of age type 2 diabetes mellitus early to moderate stage diabetic retinopathy (ETDRS: 20 (microaneurysms only) to 35 (microaneurysms/ hemorrhages and/or hard exsudates)) in one or both eyes stable HbA1c (± 0.5%) for at least 12 weeks antidiabetic treatment with either diet, metformin, DPP4, GLP1, pioglitazone, acarbose, or respective combinations HbA1c = 6.5 and = 10.0 % body mass index < 46 kg/m2 office blood pressure = 150/95 mmHg (confirmed on a second day; 24h ambulatory blood pressure measurement (ABPM) is allowed to check accuracy of office values; inclusion with 24h mean blood pressure = 145/90 mm Hg is possible); patients with hypertension should be treated according to current treatment guidelines at least 6 weeks after surgical sterilization by bilateral tubal ligation or bilateral oophorectomy hysterectomy = 50 years and in postmenopausal state > 1 year < 50 years and in postmenopausal state > 1 year with serum follicle stimulating hormone (FSH) > 40 IU/l and serum estrogen < 30 ng/l or a negative estrogen test, both at screening or women of childbearing potential with a negative serum beta human chorionic gonadotropin (ß-hCG) pregnancy test at screening who agree to meet one of the following criteria from the time of screening, during the study and for a period of 4 days following the last administration of study medication: correct use of one of the following accepted contraception methods: hormonal contraceptives (combined oral contraceptives, implants, transdermal patches, hormonal vaginal devices or injections with prolonged release), intrauterine device (IUD/IUS) or a double barrier method, e.g. condom and occlusive cap (diaphragm or cervical/vault caps) with spermicide (foam, gel, film, cream or suppository) true abstinence (periodic abstinence and withdrawal are not acceptable methods of contraception) sexual relationship only with female partners sterile male partners signed written informed consent and willingness to comply with treatment and follow-up procedures capability of understanding the investigational nature, potential risks and benefits of the clinical trial", "candidate_expression": "((< 46 kg/m2) AND (< 50 years and in postmenopausal state > 1 year with serum follicle stimulating hormone (FSH) > 40 IU/l and serum estrogen < 30 ng/l or a negative estrogen test, both at screening or women of childbearing potential with a negative serum beta human chorionic gonadotropin (ß-hCG) pregnancy test at screening who agree to meet one of the following criteria from the time of screening, during the study and for a period of 4 days following the last administration of study medication) AND (= 150/95 mmHg) AND (= 50) AND (= 6.5 and = 10.0 %) AND (> 1 year) AND (ETDRS) AND (HbA1c) AND (age) AND (antidiabetic treatment) AND (at least 12 weeks) AND (at least 6 weeks) AND (between 18 - 80 years) AND (blood pressure) AND (body mass index) AND (capability of understanding the investigational nature, potential risks and benefits of the clinical trial) AND (correct use of one of the following accepted contraception methods: hormonal contraceptives (combined oral contraceptives, implants, transdermal patches, hormonal vaginal devices or injections with prolonged release), intrauterine device (IUD/IUS) or a double barrier method, e.g. condom and occlusive cap (diaphragm or cervical/vault caps) with spermicide (foam, gel, film, cream or suppository)) AND (diabetic retinopathy) AND (eyes) AND (hysterectomy) AND (postmenopausal state) AND (signed written informed consent and willingness to comply with treatment and follow-up procedures) AND (surgical sterilization) AND (true abstinence (periodic abstinence and withdrawal are not acceptable methods of contraception)) AND (type 2 diabetes mellitus) AND (years) AND (± 0.5%) AND ((20) OR (35)) AND ((men) OR (women)) AND ((DPP4) OR (GLP1) OR (acarbose) OR (diet) OR (metformin) OR (pioglitazone)) AND ((bilateral oophorectomy) OR (bilateral tubal ligation)) AND ((early) OR (moderate stage)))"}
{"candidate_id": "LLM01911", "doc_id": "NCT02897856_inc", "case_bucket": "or", "source_criterion": "Children 6 month to 14 years who will be presented to the pediatric emergency or attended by emergency medical service who have active seizure and had no intravenous access would be eligible for the study.", "candidate_expression": "((6 month to 14 years) AND (Children) AND (active) AND (intravenous access) AND (no) AND (seizure) AND (years) AND ((attended by emergency medical service) OR (pediatric emergency)))"}
{"candidate_id": "LLM01912", "doc_id": "NCT02731794_inc", "case_bucket": "other", "source_criterion": "patients with severe left ventricle dysfunction with an ejection fraction (EF)=40%, being scheduled for revascularization.", "candidate_expression": "((being scheduled for) AND (ejection fraction (EF) =40%) AND (left ventricle dysfunction severe) AND (revascularization))"}
{"candidate_id": "LLM01913", "doc_id": "NCT02368743_exc", "case_bucket": "or", "source_criterion": "Patient included in an interventional study assessing treatment for active proctitis or distal proctosigmoiditis. Patient with left sided, colitis or pancolitis. Patient with severe proctitis (MAYO score ≥ 11 at inclusion). Patient previously treated with biologics. Patient treated with immunosuppressive within 1 month before study inclusion. Patient treated with corticosteroids within 2 weeks before study inclusion.", "candidate_expression": "((MAYO score ≥ 11 at inclusion) AND (active proctitis) AND (biologics) AND (colitis) AND (corticosteroids within 2 weeks before study inclusion) AND (distal proctosigmoiditis) AND (immunosuppressive within 1 month before study inclusion) AND (pancolitis) AND (proctitis severe) AND (treated previously) AND (treatment))"}
{"candidate_id": "LLM01914", "doc_id": "NCT02838810_inc", "case_bucket": "other", "source_criterion": "CHB patients who had received single NAs for more than 12 months. Hepatitis B e antigen (HBeAg)-negative. Hepatitis B surface antigen (HBsAg) positive and <1000 IU/mL. Hepatitis B virus DNA <100 IU/mL.", "candidate_expression": "((CHB) AND (HBeAg) AND (HBsAg) AND (Hepatitis B e antigen negative) AND (Hepatitis B surface antigen positive <1000 IU/mL) AND (Hepatitis B virus DNA <100 IU/mL) AND (NAs single more than 12 months))"}
{"candidate_id": "LLM01915", "doc_id": "NCT02316886_exc", "case_bucket": "or", "source_criterion": "Patients in whom the preferred treatment is CABG(Coronary artery bypass grafting) Stented lesion Bypass graft lesion The patients who have more than or equal to 3 target lesions 2 target lesions in the same coronary territory Heavily calcified or angulated lesion Bifurcation lesion requiring 2 stenting technique Contraindication to or planned discontinuation of dual antiplatelet therapy within 1 year Life expectancy less than 2 years Planned cardiac surgery or planned major non cardiac surgery Woman who are breastfeeding, pregnant or planning to become pregnant during the course of the study", "candidate_expression": "((Bifurcation lesion) AND (Bypass graft) AND (CABG) AND (Coronary artery bypass grafting) AND (Life expectancy less than 2 years) AND (Stented) AND (Woman) AND (dual antiplatelet therapy within 1 year) AND (lesion) AND (stenting technique 2) AND (target lesions 2 in the same coronary territory) AND (target lesions more than or equal to 3) AND ((Heavily calcified) OR (angulated)) AND ((Contraindication) OR (planned discontinuation)) AND ((cardiac surgery Planned) OR (non cardiac surgery planned major)) AND ((breastfeeding) OR (pregnant) OR (pregnant planning to become)))"}
{"candidate_id": "LLM01916", "doc_id": "NCT03016741_exc", "case_bucket": "or", "source_criterion": "Prior treatment with enzalutamide or abiraterone acetate for > 14 days prior to enrollment and completion of baseline tests. Receipt of chemotherapy for prostate or other cancer within the past 12 months with residual cognitive deficits, or receipt of chemotherapy for mCRPC. Patients/physicians planning treatment with chemotherapy during the 12 month period of the investigation are also ineligible. History of cognitive impairment or dysfunction, including a history of dementia, Alzheimer's disease, stroke with residual cognitive deficits, cognitive dysfunction related to alcohol or substance abuse, or cognitive dysfunction related to prior treatment for any cancer. Patients with a seizure history, history of recurrent falls, or known brain metastases are excluded from this clinical trial because of their poor prognosis and because of their heightened risk of seizure or progressive cognitive and/or neurologic dysfunction that would confound the evaluation. Uncontrolled intercurrent illness including, but not limited to, uncontrolled diabetes, ongoing or active infection, symptomatic congestive heart failure (New York Heart Association Class III and IV heart failure), unstable angina pectoris, cardiac arrhythmia, or psychiatric illness/social situations/substance abuse that would limit compliance with study requirements. Patients with a \"currently active\" second malignancy other than non-melanoma skin cancers are not eligible. Patients are not considered to have a \"currently active\" malignancy if they have completed all therapy and are now considered without evidence of disease for 1 year. Patients with cognitive dysfunction related to treatment of another malignancy, including a history of \"chemo-brain\", are ineligible. Patients taking psychotropic medications or illicit drugs that may alter cognition, concentration, or behavior. Appropriate treatment by a licensed provider with medications for depression or anxiety, including but not limited to SSRIs, SNRIs, and standard dose benzodiazepines at a stable dose, is permitted", "candidate_expression": "((Alzheimer's disease) AND (Class III and IV) AND (New York Heart Association) AND (Uncontrolled) AND (abiraterone acetate) AND (active) AND (alcohol abuse) AND (alter behavior) AND (alter cognition) AND (alter concentration) AND (another) AND (any) AND (brain metastases) AND (cancer) AND (cardiac arrhythmia) AND (chemotherapy) AND (cognitive dysfunction) AND (cognitive impairment) AND (congestive heart failure) AND (currently active) AND (dementia) AND (diabetes) AND (enrollment) AND (enzalutamide) AND (for > 14 days) AND (heart failure) AND (history) AND (history of) AND (illicit drugs) AND (infection) AND (intercurrent illness) AND (mCRPC) AND (malignancy) AND (non-melanoma skin cancers) AND (ongoing) AND (other) AND (other than) AND (prior) AND (prior to enrollment) AND (prostate cancer) AND (psychiatric illness) AND (psychotropic medications) AND (recurrent falls) AND (residual cognitive deficits) AND (second) AND (seizure) AND (social situations) AND (stroke) AND (substance abuse) AND (symptomatic) AND (treatment) AND (uncontrolled) AND (unstable angina pectoris) AND (within the past 12 months))"}
{"candidate_id": "LLM01917", "doc_id": "NCT01994382_inc", "case_bucket": "or", "source_criterion": "Phase 1 Specific Patient at least 18yrs of age with histologically confirmed CLL/SLL or B-cell Non-Hodgkin lymphoma (DLBCL, FL, MCL, MZL, lymphoplasmacytic lymphoma). Phase 2a Inclusion Histological evidence: FL Grade 1-3A/iNHL, with relapsed or refractory disease (iNHL includes LPL/WM, MZL); aNHL, defined as DLBCL, FL Grade 3B, MCL, and transformed NHL with relapsed disease; CLL/SLL, PTCL, or CTCL (with MF/SS) with relapsed or refractory. Received BCR and/or BCL2 inhibitors were intolerant or had relapsed/refractory disease afterwards. Prior treatment for lymphoid malignancy for progressive /refractory disease ≥ 1 prior regimen (min 2 cycles) with antibody conjugate, cytotoxic chemotherapy, or TKI alone or in combination. Measureable disease defined as: ≥ 1 lesion ≥ 1.5 cm single dimension via CT, CT/PET with nodal or mass lesions; Quantifiable circulating tumor cells; or for Waldenström's macroglobulinemia presence of IgM l > 2X ULN; For CTCL: mSWAT > 0 Ability to provide diagnostic reports General Inclusion ECOG Score of 0 or 1. Hematologic ANC > 1000/uL and platelet > 75,000/uL, Serum creatinine of < 1.5 ULN or calculated CrCl of > 50 mL/min Bilirubin < 20.0mg/dL (if Gilberts then < 2.5 mg/dL) and AST/AST < 2.5 ULN", "candidate_expression": "((AST/AST < 2.5 ULN) AND (Bilirubin) AND (DLBCL) AND (ECOG Score 0 or 1) AND (FL) AND (Grade 1-3A) AND (Hematologic ANC > 1000/uL) AND (Histological) AND (IgM l > 2X ULN) AND (MCL) AND (MZL) AND (Measureable disease ≥ 1 lesion) AND (age at least 18yrs) AND (histologically confirmed) AND (intolerant) AND (lymphoid malignancy) AND (lymphoplasmacytic lymphoma) AND (mSWAT > 0) AND (platelet > 75,000/uL) AND (relapsed disease) AND (≥ 1.5 cm single dimension ≥ 1.5 cm) AND ((FL) OR (iNHL)) AND ((refractory disease) OR (relapsed disease)) AND ((LPL) OR (MZL) OR (WM)) AND ((B-cell Non-Hodgkin lymphoma) OR (CLL) OR (SLL)) AND ((DLBCL) OR (FL) OR (Grade 3B) OR (MCL) OR (transformed NHL)) AND ((CLL) OR (CTCL) OR (PTCL) OR (SLL) OR (aNHL) OR (iNHL)) AND ((MF) OR (SS)) AND ((BCL2 inhibitors) OR (BCR inhibitors)) AND ((refractory disease) OR (relapsed)) AND ((Prior) OR (treatment)) AND ((progressive disease) OR (refractory disease)) AND ((TKI) OR (antibody conjugate) OR (cytotoxic chemotherapy)) AND ((CT) OR (CT/PET)) AND ((mass lesions) OR (nodal lesions)) AND ((CTCL) OR (Waldenström's macroglobulinemia) OR (circulating tumor cells)) AND ((Serum creatinine < 1.5 ULN) OR (calculated CrCl > 50 mL/min)) AND ((< 20.0mg/dL) OR (Gilberts < 2.5 mg/dL)))"}
{"candidate_id": "LLM01918", "doc_id": "NCT02589977_inc", "case_bucket": "or", "source_criterion": "estimated glomerular filtration rate (eGFR) > 60 ml/min preserved left ventricular ejection fraction (>= 50%) on echocardiography HEALTHY: normal cardiac structure and function on echocardiography, BP < 140/90 HYPERTENSIVE: history of BP >140/90, 1 or more antihypertensive medications, LV ejection fraction (LVEF) at least 50%, current BP < 160/90 HFpEF: physician-confirmed diagnosis of HF, symptomatic HF, LVEF at least 50%, elevated LV filling pressure by catheterization, echocardiographic criteria or B-type-natriuretic peptide > 100, current BP < 160/90", "candidate_expression": "((B-type-natriuretic peptide > 100) AND (BP < 140/90) AND (BP >140/90) AND (BP current < 160/90) AND (HEALTHY normal cardiac structure normal cardiac function) AND (HF physician-confirmed) AND (HF symptomatic) AND (HFpEF) AND (HYPERTENSIVE) AND (LV ejection fraction (LVEF) at least 50%) AND (LV filling pressure elevated) AND (LVEF at least 50%) AND (antihypertensive medications 1 or more) AND (catheterization) AND (current BP < 160/90) AND (echocardiography) AND (estimated glomerular filtration rate (eGFR) > 60 ml/min) AND (history) AND (left ventricular ejection fraction preserved >= 50%))"}
{"candidate_id": "LLM01919", "doc_id": "NCT02668016_exc", "case_bucket": "or", "source_criterion": "History of neuropathy Regularly taking prescribed analgesia History of a chronic pain condition History of severe mental illness (as their experience of symptoms may already be altered) Current use of fibrates (because of the risk of interaction with statins but will not exclude participants taking ezetimibe). Severe previous reaction or reaction considered immunological, such as anaphylaxis, facial swelling, severe rash, muscle ache with rise in serum creatine kinase, inflammatory myopathy, rhabdomyolysis or liver function abnormalities (aspartate transaminase (AST) or alanine transaminase (ALT) greater than 3 times upper limit or normal). Side-effects taking longer than 2 weeks to develop (because in such participants much longer blocks of treatment would be required, if the present study is positive such studies will be planned for the future)*. History of statin intolerance with drug interaction to antiretroviral drugs. History of statin intolerance to any other drug. Pregnant or breast feeding. Side effects taking longer than 2 weeks to present. In clinical judgement of study doctor, participant should not participate.", "candidate_expression": "((ALT) AND (AST) AND (Pregnant or breast feeding) AND (Regularly) AND (alanine transaminase) AND (analgesia) AND (anaphylaxis) AND (antiretroviral drugs) AND (aspartate transaminase) AND (chronic pain) AND (facial swelling,) AND (fibrates) AND (greater than 3 times upper limit or normal) AND (inflammatory myopathy) AND (intolerance) AND (liver function abnormalities) AND (mental illness) AND (muscle ache) AND (neuropathy) AND (rhabdomyolysis) AND (rise) AND (serum creatine kinase) AND (severe) AND (severe rash) AND (statin))"}
{"candidate_id": "LLM01920", "doc_id": "NCT02867618_inc", "case_bucket": "or", "source_criterion": "Phase I: Patients must have histologically confirmed R/R NHL or HL (defined by WHO criteria). Patients with chronic lymphocytic leukemia (CLL) and small lymphocytic lymphoma (SLL) are eligible. In addition, patients with NHL other than diffuse large B cell lymphomas (DLBCL) must have received at least 2 prior therapies. Patients with DLBCL and HL will be eligible if there is no available standard therapy. Phase II: Patients must have histologically confirmed R/R NHL (as defined by WHO criteria). Patients with NHL other than diffuse large B cell lymphomas (DLBCL) must have received at least 2 prior therapies. Patients with DLBCL will be eligible if there is no available standard therapy. Must have received front line chemotherapy. No upper limit for the number of prior therapies Evaluable Disease in the Phase I, and measurable disease in the Phase II Age > 18 years ECOG performance status < 2 Patients must have adequate organ and marrow function Adequate Contraception Ability to understand and the willingness to sign a written informed consent document", "candidate_expression": "((Ability to understand and the willingness to sign a written informed consent document) AND (Adequate) AND (Age > 18 years in the Phase II) AND (Contraception Adequate) AND (DLBCL) AND (Disease measurable in the Phase I) AND (ECOG performance status < 2) AND (HL) AND (NHL) AND (NHL R/R) AND (WHO criteria) AND (adequate) AND (chemotherapy front line) AND (chronic lymphocytic leukemia (CLL)) AND (histologically confirmed) AND (marrow function adequate) AND (organ function adequate) AND (small lymphocytic lymphoma (SLL)) AND (therapies at least 2 prior) AND NOT (diffuse large B cell lymphomas (DLBCL)) AND NOT (standard therapy))"}
{"candidate_id": "LLM01921", "doc_id": "NCT01816997_inc", "case_bucket": "other", "source_criterion": "Age 35-70 years old Fasting blood glucose 100-125 mg/dL", "candidate_expression": "((100-125 mg/dL) AND (35-70 years old) AND (Age) AND (Fasting blood glucose))"}
{"candidate_id": "LLM01922", "doc_id": "NCT02969876_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01923", "doc_id": "NCT03513757_exc", "case_bucket": "or", "source_criterion": "Inpatient status, airway abnormalities, allergy to any study medications, eggs and soy, and mitochondrial disorders. All subjects with any cardiac disease or history of cardiac arrhythmias will be excluded.", "candidate_expression": "(((Inpatient status) OR (airway abnormalities) OR (allergy) OR (mitochondrial disorders)) AND ((cardiac arrhythmias history) OR (cardiac disease)) AND ((eggs) OR (soy) OR (study medications)))"}
{"candidate_id": "LLM01924", "doc_id": "NCT02950558_exc", "case_bucket": "or", "source_criterion": "Unable to give informed consent in English Unable to complete surveys in English Unable to understand instructions for using pump in English Unavailable for followup Polytrauma; undergoing other surgeries or having other orthopedic injuries related to the precipitating cause of the ankle fracture Infection Peripheral vascular disease Diabetes Currently undergoing chemotherapy Pregnancy Currently lactating Heart disease or heart rhythm disorder or taking anti-arrhythmic drugs Severe renal impairment (Class 3 or worse kidney disease) Liver disease (cirrhosis or liver failure) Prior allergic reaction to any type of local anesthetic Taking therapeutic doses of anti-coagulants or anti-platelet therapy (prophylactic doses started because of hospital admission are not an exclusion) Currently taking antidepressants or other psychiatric medications Single shot local nerve block prior to surgery was ineffective Selected for neuraxial anesthesia rather than general anesthesia for the open reduction surgery Already receiving chronic analgesic therapy for a separate chronic pain condition", "candidate_expression": "((Currently lactating) AND (Diabetes) AND (Infection) AND (Liver disease) AND (Peripheral vascular disease) AND (Polytrauma) AND (Pregnancy) AND (Severe renal impairment) AND (Unable to complete surveys in English) AND (Unable to give informed consent in English) AND (Unable to understand instructions for using pump in English) AND (Unavailable for followup) AND (allergic reaction) AND (analgesic therapy chronic) AND (ankle fracture) AND (chemotherapy) AND (chronic pain separate) AND (general anesthesia) AND (local anesthetic) AND (local nerve block Single shot prior to surgery) AND (neuraxial anesthesia) AND (not) AND (open reduction surgery) AND (rather than) AND ((Heart disease) OR (anti-arrhythmic drugs) OR (heart rhythm disorder)) AND ((cirrhosis) OR (liver failure)) AND ((anti-coagulants) OR (anti-platelet therapy)) AND ((antidepressants) OR (psychiatric medications)) AND ((other orthopedic injuries) OR (other surgeries)))"}
{"candidate_id": "LLM01925", "doc_id": "NCT02704234_exc", "case_bucket": "other", "source_criterion": "pregnancy menopause interstitial cystitis irritable bowel syndrome untreated vaginitis cervicitis pelvic inflammatory disease any other pelvic pathology causing pain concomitant physical therapy concomitant biofeedback concomitant massage additional acupuncture", "candidate_expression": "((acupuncture) AND (biofeedback) AND (causing pain) AND (cervicitis) AND (concomitant) AND (interstitial cystitis) AND (irritable bowel syndrome) AND (massage) AND (menopause) AND (pelvic inflammatory disease) AND (pelvic pathology) AND (physical therapy) AND (pregnancy) AND (untreated vaginitis))"}
```
