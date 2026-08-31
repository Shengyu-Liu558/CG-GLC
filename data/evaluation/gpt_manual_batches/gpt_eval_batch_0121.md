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
{"candidate_id": "LLM03001", "doc_id": "NCT02959801_inc", "case_bucket": "other", "source_criterion": "proven acute deep venous thrombosis, less than 21 days and who were referred to the interventional radiology department.", "candidate_expression": "((acute) AND (deep venous thrombosis) AND (interventional radiology department) AND (less than 21 days) AND (proven) AND (referred to))"}
{"candidate_id": "LLM03002", "doc_id": "NCT02334722_exc", "case_bucket": "or", "source_criterion": "No known history of seizure activity. Pregnant or breastfeeding. Renal dysfunction (CrCl < 30ml/min). Beck's Depression Inventory (BDI) =14 Allergy to levetiracetam.", "candidate_expression": "((< 30ml/min) AND (=14) AND (Allergy) AND (Beck's Depression Inventory (BDI)) AND (CrCl) AND (No) AND (Renal dysfunction) AND (history) AND (levetiracetam) AND (seizure activity) AND ((Pregnant) OR (breastfeeding)))"}
{"candidate_id": "LLM03003", "doc_id": "NCT02802644_inc", "case_bucket": "other", "source_criterion": "Non-ST segement elevation acute coronary syndrome", "candidate_expression": "((Non-ST segement elevation) AND (acute coronary syndrome))"}
{"candidate_id": "LLM03004", "doc_id": "NCT03223909_exc", "case_bucket": "or", "source_criterion": "Subjects with topical and/or systemic medication or mechanical devices that interfere determinedly on the results of the study (such as topical immunomodulators, punctal plugs, corticosteroids, preservative artificial tears, contact lenses). Subjects (females) with active sexual life that do not use a contraceptive method. Female subjects who are pregnant or lactating Female subjects with a positive urine pregnancy test Positive drug addictions* (verbal interrogatory) Subjects who have participated on any other research clinical trials on the last 40 days Subjects legal or mentally disabled to give an informed consent for participating on this study Subjects who can't comply with the appointments or with every protocol requirement. Serious tear film dysfunction syndrome TBUT < 5 s Schirmer: < 4 mm OSDI > 30 pints Corneal staining > grade III on the Oxford scale Non perforated corneal ulcer Perforated corneal ulcer Autoimmune corneal ulcer Ocular surface scarring diseases Ocular surface or annexes metaplastic lesions Fibro vascular proliferation lesions on the conjunctival and/or corneal surface (i.e.: pterygium) Concomitant chronic inflammatory diseases on any ocular structure Acute or infectious inflammatory disease Corneal disease potentially requiring a treatment during the following 3 months Use of topical or systemic drug products classified as forbidden Ocular surgical procedures 3 months before the protocol inclusion Treatments or procedures indicated on the tear film dysfunction treatment, as punctal silicone plugs. Posterior segment diseases requiring a treatment or threatening the visual prognosis Retinal diseases potentially requiring treatment during the following 3 months History of penetrating keratoplasty. Soft or hard contact lenses use during the last month from inclusion day", "candidate_expression": "((Corneal disease) AND (Corneal staining > grade III Oxford scale) AND (Female) AND (Fibro vascular proliferation lesions pterygium) AND (OSDI > 30 pints) AND (Ocular surface scarring diseases) AND (Ocular surgical procedures 3 months before the protocol inclusion 3 months before the protocol inclusion) AND (Positive drug addictions) AND (Posterior segment diseases) AND (Retinal diseases) AND (Schirmer < 4 mm) AND (Serious tear film dysfunction syndrome) AND (Subjects legal or mentally disabled to give an informed consent for participating on this study) AND (Subjects who have participated on any other research clinical trials on the last 40 days) AND (TBUT < 5 s) AND (active sexual life) AND (chronic inflammatory diseases Concomitant ocular structure) AND (corneal ulcer Autoimmune) AND (corneal ulcer Non perforated) AND (corneal ulcer Perforated) AND (females) AND (inflammatory disease) AND (penetrating keratoplasty History) AND (punctal silicone plugs) AND (tear film dysfunction treatment) AND (treatment potentially requiring during the following 3 months) AND (treatment requiring during the following 3 months) AND (urine pregnancy test positive) AND (verbal interrogatory) AND NOT (contraceptive method) AND ((lactating) OR (pregnant)) AND ((legal disabled) OR (mentally disabled)) AND ((mechanical devices) OR (systemic medication) OR (topical medication)) AND ((annexes metaplastic lesions Ocular) OR (lesions Ocular surface)) AND ((conjunctival) OR (corneal surface)) AND ((Acute) OR (infectious)) AND ((Treatments) OR (procedures)) AND ((contact lenses) OR (corticosteroids) OR (preservative artificial tears) OR (punctal plugs) OR (topical immunomodulators)) AND ((threatening the visual prognosis) OR (treatment requiring)) AND ((Soft contact lenses) OR (hard contact lenses)))"}
{"candidate_id": "LLM03005", "doc_id": "NCT03187639_exc", "case_bucket": "or", "source_criterion": "Atrial fibrillation of new onset or when rate control has been difficult Known bigemini/trigeminy Prior CABG surgery Allergic to contrast Advanced renal impairment Significant valve disease (severe aortic stenosis or regurgitation; severe mitral regurgitation) Life expectancy <12 months Inclusion in another trial without prior agreement with CI", "candidate_expression": "((Advanced renal impairment) AND (Allergic) AND (CABG surgery Prior) AND (Inclusion in another trial without prior agreement with CI) AND (Life expectancy <12 months) AND (contrast) AND (mitral regurgitation severe) AND (valve disease) AND ((Atrial fibrillation new onset) OR (rate control has been difficult)) AND ((aortic stenosis) OR (regurgitation)) AND ((bigemini) OR (trigeminy)))"}
{"candidate_id": "LLM03006", "doc_id": "NCT02525991_inc", "case_bucket": "or", "source_criterion": "Male and female patients between the ages of 18-65 years, inclusive Patients (or legal representative) willing and able to provide written Informed Consent Form. Psychiatric patients already diagnosed of schizophrenia or bipolar disorder, according to the Diagnostic and Statistical Manual of Mental Disorders- IV, Diagnostic and Statistical Manual of Mental Disorders- V or International Code of Disease criteria. Patients with an on-going agitation episode, or with a previous one within the 6 months prior to screening, attended and managed in the hospital setting. Previously treated with ADASUVE® with a positive outcome (responders) according to (CGI-I) scale (defined as having a CGI-I score of 1 or 2 at 2 hours after administration of the inhalation) Patients free of active respiratory disease such as acute respiratory signs/symptoms (e.g., wheezing) or with active airways disease (asthma, chronic obstructive pulmonary disease or emphysema). Requirement of family or other caregiver support at study investigator criteria (defined as a patient's relative or caregiver (male or female) = 80 year old, who spend = 3 consecutive hours with patient, with good physical and psychological health status and without physical limitations, reading and writing educational level and able to understand and follow the study procedures). Availability of patient's medical records data about the previous treatment with ADASUVE® at hospital setting. If a female is of childbearing potential and sexually active (except if female is surgically sterile or post-menopausal with history of no menses for at least 24 months), patient must be non-lactating and non-pregnant (with a negative pregnancy test result at baseline visit) and have to agree to use a medically acceptable and effective birth control method throughout the study and for one week following the end of the study.", "candidate_expression": "((ADASUVE) AND (CGI-I score 1 or 2 2 hours after administration of the inhalation)) AND (Diagnostic and Statistical Manual of Mental Disorders- IV) AND (Diagnostic and Statistical Manual of Mental Disorders- V) AND (If a female is of childbearing potential and sexually active (except if female is surgically sterile or post-menopausal with history of no menses for at least 24 months), patient must be non-lactating and non-pregnant (with a negative pregnancy test result at baseline visit) and have to agree to use a medically acceptable and effective birth control method throughout the study and for one week following the end of the study) AND (International Code of Disease criteria) AND (Male) AND (Patients (or legal representative) willing and able to provide written Informed Consent Form) AND (acute respiratory signs) AND (acute respiratory symptoms) AND (ages 18-65 years) AND (agitation episode within the 6 months prior to screening) AND (asthma) AND (bipolar disorder) AND (chronic obstructive pulmonary disease) AND (emphysema) AND (female) AND (schizophrenia) AND (wheezing) AND NOT (respiratory disease active) AND NOT (airways disease active))"}
{"candidate_id": "LLM03007", "doc_id": "NCT01891383_inc", "case_bucket": "or", "source_criterion": "Cases (with a history of TBI): 1. Ages 50-95 years 2. History of traumatic brain injury of sufficient severity to have resulted in medical attention (ascertained via the Ohio State University TBI Identification Questionnaire—OSU TBI-ID, and based on DoD/VA criteria) 3. Residence in AFRH-Washington D.C. or the Veterans Home of California-Yountville 4. MMSE score ≥ 20 5. Capacity to provide consent to participate in research (assessment made by study physician) 6. Ability to read and write English Controls (without a history of TBI): 1. Ages 50-95 years 2. No history of traumatic brain injury of sufficient severity to have resulted in medical attention (ascertained via the Ohio State University TBI Identification Questionnaire—OSU TBI-ID) 3. Residence in AFRH-Washington or the Veterans Home of California-Yountville 4. MMSE score ≥ 20 5. Capacity to provide consent or assent to participate in research 6. Ability to read and write English -", "candidate_expression": "((AFRH-Washington) AND (AFRH-Washington D.C.) AND (Ability to read and write English) AND (Ability to read and write English -) AND (Ages 50-95 years) AND (Capacity to provide consent or assent to participate in research) AND (Capacity to provide consent to participate in research (assessment made by study physician)) AND (MMSE score ≥ 20) AND (Ohio State University TBI Identification Questionnaire—OSU TBI-ID sufficient severity) AND (Veterans Home of California-Yountville) AND (sufficient severity) AND (traumatic brain injury History sufficient severity) AND NOT (traumatic brain injury history sufficient severity))"}
{"candidate_id": "LLM03008", "doc_id": "NCT02295202_inc", "case_bucket": "other", "source_criterion": "Metabolic Syndrome (ATP III) Moderate to severe OSA", "candidate_expression": "((ATP) AND (III) AND (Metabolic Syndrome) AND (Moderate to severe) AND (OSA))"}
{"candidate_id": "LLM03009", "doc_id": "NCT03234816_inc", "case_bucket": "other", "source_criterion": "full term singleton pregnant women Scheduled for elective Cesarean Delivery Aged between 18 and 40 years", "candidate_expression": "((Aged) AND (Cesarean Delivery) AND (Scheduled for) AND (between 18 and 40 years) AND (elective) AND (full term) AND (pregnant) AND (singleton) AND (women))"}
{"candidate_id": "LLM03010", "doc_id": "NCT02701777_exc", "case_bucket": "or", "source_criterion": "Uncontrolled medical problems including pulmonary, cardiovascular or orthopedic disease Any debilitating disease prior to the SCI that caused exercise intolerance Premorbid, ongoing major depression or psychosis, altered cognitive status History of head injury or stroke Metal plate in skull History of seizures Receiving drugs acting primarily on the central nervous system, which lower the seizure threshold (see appendix 2) Pregnant females Ongoing cord compression or a syrinx in the spinal cord or who suffer from a spinal cord disease such as spinal stenosis, spina bifida, MS, or herniated disk Individuals with scalp shrapnel, cochlear implants, or aneurysm clips.", "candidate_expression": "((Metal plate in skull) AND (Pregnant) AND (altered cognitive status) AND (debilitating disease prior to the SCI) AND (drugs acting primarily on the central nervous system lower the seizure threshold) AND (exercise intolerance) AND (females) AND (medical problems Uncontrolled) AND (seizures History) AND ((major depression) OR (psychosis)) AND ((head injury) OR (stroke)) AND ((cord compression) OR (spinal cord disease) OR (syrinx spinal cord)) AND ((MS) OR (herniated disk) OR (spina bifida) OR (spinal stenosis)) AND ((aneurysm clips) OR (cochlear implants) OR (scalp shrapnel)) AND ((cardiovascular disease) OR (orthopedic disease) OR (pulmonary disease)))"}
{"candidate_id": "LLM03011", "doc_id": "NCT02361905_inc", "case_bucket": "other", "source_criterion": "hypoechoic uterine leiomyoma (echogenicity <3), intramural leiomyomas with an ultrasonographic size <20 cm but >4cm, indication to surgery (symptoms of menometrorrhagia, menstrual disorder, infertility, pelvic pain or pelvic pressure", "candidate_expression": "((<20 cm but >4cm) AND (<3) AND (echogenicity) AND (hypoechoic) AND (indication to) AND (infertility) AND (intramural leiomyomas) AND (menometrorrhagia) AND (menstrual disorder) AND (pelvic pain) AND (pelvic pressure) AND (surgery) AND (ultrasonographic size) AND (uterine leiomyoma))"}
{"candidate_id": "LLM03012", "doc_id": "NCT03216447_exc", "case_bucket": "or", "source_criterion": "Patient has previously received or is receiving an organ transplant other than a liver. Patient currently requires dialysis Recipient or donor is known to be seropositive for human immunodeficiency virus (HIV) Patient has received a liver transplant from a non-heart beating donor Patient who is HCV negative has received an HCV positive (HCV RNA by PCR or HCV antibody) donor liver Patient who is HbsAg negative has received an HbsAg positive (HBV DNA by PCR or HBV antibody) donor liver Patient has received a liver transplant from a decrease donor > 70 years of age Patient has a current malignancy or a history of malignancy (within the past 5 years), except hepatocellular carcinoma within UCSF Criteria and basal or non-metastatic squamous cell carcinoma of skin that has been treated successfully. Patient is hemodynamically unstable on POD 15", "candidate_expression": "((> 70 years) AND (HBV DNA) AND (HCV) AND (HIV) AND (HbsAg) AND (PCR) AND (POD 15) AND (UCSF Criteria) AND (age) AND (dialysis) AND (donor) AND (except) AND (heart beating) AND (hemodynamically unstable) AND (hepatocellular carcinoma) AND (human immunodeficiency virus) AND (liver) AND (liver transplant) AND (negative) AND (non) AND (non-metastatic) AND (organ transplant) AND (other than) AND (positive) AND (seropositive) AND (treated successfully) AND (within the past 5 years) AND ((HCV RNA) OR (HCV antibody)) AND ((HBV antibody) OR (PCR)) AND ((history of malignancy) OR (malignancy)) AND ((basal cell carcinoma of skin) OR (squamous cell carcinoma of skin)) AND ((Recipient) OR (donor)))"}
{"candidate_id": "LLM03013", "doc_id": "NCT03192020_exc", "case_bucket": "or", "source_criterion": "recurrent contracture in the finger to be treated neurologic condition causing the loss of function of the finger to be treated contraindication for collagenase clostridium histolyticym (Xiapex/Xiaflex ®) pregnant or breast feeding TPED > 135° (Tubiana stage 4) in finger to be treated rheumatoid arthritis previous fracture in finger to be treated, which affects range of motion of MP or PIP joint age > 80 years", "candidate_expression": "((> 135°) AND (> 80 years) AND (MP joint) AND (PIP joint) AND (TPED) AND (Tubiana) AND (Xiaflex) AND (Xiapex) AND (affects range of motion) AND (age) AND (breast feeding) AND (collagenase clostridium histolyticym) AND (contracture) AND (contraindication) AND (finger to be treated) AND (fracture) AND (loss of function) AND (neurologic condition) AND (pregnant) AND (previous) AND (recurrent) AND (rheumatoid arthritis) AND (stage 4))"}
{"candidate_id": "LLM03014", "doc_id": "NCT00989261_exc", "case_bucket": "or", "source_criterion": "1. Patients over the age of 85 years except at the discretion of the Investigator and with agreement of the Sponsor. 2. Diagnosis of acute promyelocytic leukemia 3. Diagnosis of chronic myelogenous leukemia (CML) in blast crisis 4. AML in relapse or refractory after 3 or more previous lines of chemotherapy (and/or HSCT) treatment 5. AML or antecedent MDS secondary to prior chemotherapy 6. Persistent clinically significant non-hematological toxicity that is Grade >1 by NCI CTCAE v4 from prior chemotherapy 7. Patients who have had HSCT and are within 100 days of transplant and/or are still taking immunosuppressive drugs and/or have clinically significant graft-versus-host disease requiring treatment and/or have >Grade 1 persistent non hematological toxicity related to the transplant 8. Clinically active central nervous system (CNS) leukemia. Patients with CNS leukemia, which is controlled, but who are still receiving IT therapy at study entry may be considered eligible and continue receive IT therapy at the discretion of the Investigator and with agreement of the Sponsor. 9. Patients who have previously received AC220 10. Disseminated intravascular coagulation (DIC) (diagnosis by laboratory or clinical assessment) 11. Major surgery within 4 weeks prior to enrollment in the study 12. Radiation therapy within 4 weeks prior to, or concurrent with study 13. Use of concomitant drugs that prolong QT/QTc interval and/or are CYP3A4 inhibitors are prohibited with the exception of antibiotics, antifungals, and other antimicrobials that are used as standard of care to prevent or treat infections and other such drugs that are considered absolutely essential for the care of the patient. 14. Uncontrolled or significant cardiovascular disease 15. Women who are pregnant, lactating, or unwilling to use contraception if of childbearing potential 16. Men who are unwilling to use contraception if their partners are of childbearing potential 17. Active, uncontrolled infection 18. Human immunodeficiency virus positivity 19. Active hepatitis B or C or other active liver disease 20. History of cancer, except Stage 1 cervix or nonmelanotic skin cancer, with the possible exception of patients in complete remission", "candidate_expression": "((AC220) AND (AML) AND (AML in relapse refractory) AND (CYP3A4 inhibitors) AND (Disseminated intravascular coagulation (DIC)) AND (HSCT have had within 100 days of transplant) AND (Human immunodeficiency virus) AND (Human immunodeficiency virus positivity) AND (MDS antecedent) AND (Major surgery within 4 weeks prior to enrollment enrollment) AND (Men) AND (NCI CTCAE v4 Grade >1) AND (Patients over the age of 85 years except at the discretion of the Investigator and with agreement of the Sponsor.) AND (Radiation therapy within 4 weeks prior to study concurrent with study study) AND (acute promyelocytic leukemia) AND (age over the age of 85 years) AND (antibiotics) AND (antifungals) AND (antimicrobials) AND (at the discretion of the Investigator) AND (blast crisis) AND (cancer History) AND (cardiovascular disease Uncontrolled significant) AND (central nervous system (CNS) leukemia) AND (chemotherapy prior) AND (childbearing potential) AND (chronic myelogenous leukemia (CML)) AND (clinically significant) AND (contraception unwilling) AND (drugs that prolong QT/QTc interval that prolong QT/QTc interval) AND (graft-versus-host disease clinically significant) AND (hepatitis B) AND (hepatitis C) AND (immunosuppressive drugs still) AND (infection Active uncontrolled) AND (lactating) AND (lines of chemotherapy 3 or more previous) AND (liver disease active) AND (pregnant) AND (prolong QT/QTc interval) AND (their partners are of childbearing potential) AND (toxicity >Grade 1 persistent non hematological) AND (toxicity clinically significant non-hematological Grade >1 by NCI CTCAE v4) AND (transplant) AND (transplant transplant) AND (treatment requiring persistent) AND NOT (skin cancer Stage 1 cervix nonmelanotic))"}
{"candidate_id": "LLM03015", "doc_id": "NCT02195024_inc", "case_bucket": "or", "source_criterion": "Approved clinical indication for pectoral pacemaker exchange (e.g. elective replacement indication (ERI), end of service (EOS)) a single or dual chamber MRI conditional pacemaker (BSCI) or Any comparable successor IPG (MRI conditional system, BSCI) compatible with Implanted Fineline-II-leads (BSCI), MRI conditional The ascertained lead impedance is between 200 and 1500 Ohm. All pacing capture thresholds (PCT) do not exceed 2.0 V @0.4 or 0.5 ms in pacemaker dependent patients Male or female 18 years or older Understand the nature of the procedure Give written informed consent Able to complete all testing required by the clinical protocol Ability to measure atrial and/or ventricular pacing threshold(s) at 0.4 or 0.5 ms Patient body height greater or equal to 140 cm Pectoral implanted device Subjects who are able and willing to undergo elective cardiac magnetic resonance (MR) scanning without sedation (MRI-group) Subjects who are geographically stable and available for follow-up at the study center for the length of the study", "candidate_expression": "((Ability to measure atrial and/or ventricular pacing threshold(s) at 0.4 or 0.5 ms) AND (Able to complete all testing required by the clinical protocol) AND (BSCI) AND (Give written informed consent) AND (Implanted Fineline-II-leads) AND (MR) AND (MRI conditional system) AND (Male) AND (PCT) AND (Pectoral implanted device) AND (ascertained lead impedance between 200 and 1500 Ohm) AND (at the study center for the length of the study) AND (available for follow-up) AND (body height greater or equal to 140 cm) AND (cardiac magnetic resonance scanning willing to undergo elective without sedation) AND (clinical indication) AND (elective replacement indication (ERI)) AND (end of service (EOS) single chamber dual chamber) AND (female) AND (geographically stable) AND (pacemaker MRI conditional) AND (pacemaker dependent) AND (pacing capture thresholds) AND (pectoral pacemaker exchange) AND (successor IPG comparable) AND (years or older 18 years or older))"}
{"candidate_id": "LLM03016", "doc_id": "NCT02570347_exc", "case_bucket": "or", "source_criterion": "Upper limb bites Multiple (> 1) bites Wound manipulation Extensive local necrosis or blebs Seriously-ill patients with hypotension/capillary leak/life threatening bleeding. Suspected cobra bite, OR Pregnant/breast-feeding women", "candidate_expression": "((> 1) AND (Multiple) AND (Seriously-ill) AND (Suspected) AND (Upper limb) AND (Wound manipulation) AND (bites) AND (cobra bite) AND (life threatening) AND (women) AND ((bleeding) OR (capillary leak) OR (hypotension)) AND ((Pregnant) OR (breast-feeding)) AND ((Extensive local blebs) OR (Extensive local necrosis)))"}
{"candidate_id": "LLM03017", "doc_id": "NCT00639795_inc", "case_bucket": "other", "source_criterion": "Age greater than 18 Planned thoracoscopy with low probability(by surgeon estimate) of conversion to open procedure", "candidate_expression": "((Age) AND (greater than 18) AND (low probability(by surgeon estimate) of conversion to open procedure) AND (thoracoscopy))"}
{"candidate_id": "LLM03018", "doc_id": "NCT01261832_inc", "case_bucket": "other", "source_criterion": "Acute Myocardial Infarction Undergoing Primary percutaneous coronary intervention.", "candidate_expression": "((Acute Myocardial Infarction) AND (Primary percutaneous coronary intervention))"}
{"candidate_id": "LLM03019", "doc_id": "NCT03263481_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03020", "doc_id": "NCT02973035_exc", "case_bucket": "or", "source_criterion": "Unwillingness or inability to comply with the procedures described in this protocol Planned cardiac surgery or planned major non-cardiac surgery within the study period. Stroke or coronary revascularization in the past 6 months. Clinically significant pulmonary disease. Untreated hyperthyroidism, or hypothyroidism. A diagnosis of cancer (other than superficial squamous or basal cell skin cancer) in the past 3 years or current treatment for the active cancer. Female of child-bearing potential who do not use adequate contraception and women who are pregnant or breast-feeding Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study. LV ejection fraction < 50%. Significant renal disease manifested by serum creatinine > 2.5 mg/dL Hepatic disease or biliary tract obstruction, or significant hepatic enzyme elevation (ALT or AST > 3 times upper limit of normal). History of intolerance to ARB or amlodipine. Hypertrophic or restrictive cardiomyopathy. Moderate or severe valvular disease. Constrictive pericarditis Atrial fibrillation with a heart rate > 120/min. Sitting systolic BP < 100 mmHg", "candidate_expression": "((< 100 mmHg) AND (< 50%) AND (> 120/min) AND (> 2.5 mg/dL) AND (> 3 times upper limit of normal) AND (ALT) AND (ARB) AND (AST) AND (Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study) AND (Atrial fibrillation) AND (Clinically significant) AND (Constrictive pericarditis) AND (Female of child-bearing potential who do not use adequate contraception and women who are pregnant or breast-feeding) AND (Hepatic disease) AND (Hypertrophic cardiomyopathy) AND (LV ejection fraction) AND (Moderate) AND (Planned) AND (Significant) AND (Sitting) AND (Stroke revascularization) AND (Untreated) AND (Unwillingness or inability to comply with the procedures described in this protocol) AND (active) AND (amlodipine) AND (basal cell skin cancer) AND (biliary tract obstruction) AND (cancer) AND (cardiac) AND (cardiac surgery) AND (coronary revascularization) AND (heart rate) AND (hepatic enzyme elevation) AND (hyperthyroidism) AND (hypothyroidism) AND (in the past 3 years) AND (in the past 6 months) AND (intolerance) AND (major) AND (non) AND (other than) AND (planned) AND (pulmonary disease) AND (renal disease) AND (restrictive cardiomyopathy) AND (serum creatinine) AND (severe) AND (significant) AND (study period) AND (superficial squamous skin cancer) AND (surgery) AND (systolic BP) AND (treatment) AND (valvular disease) AND (within the study period))"}
{"candidate_id": "LLM03021", "doc_id": "NCT03541980_exc", "case_bucket": "or", "source_criterion": "Patient with fever (38C or 100.4F) Patient less than age 4 years Patient greater than age 16 years Patient with hypersensitivity/allergy to either morphine, NSAIDs, or acetaminophen Patient received acetaminophen within the past 4 hours Patient with known liver disease or renal disease Patient not requiring IV morphine (pain score 5/10 or less) Patient enrolled in the study within the past 72 hours", "candidate_expression": "((100.4F) AND (38C) AND (5/10 or less) AND (IV morphine) AND (NSAIDs) AND (acetaminophen) AND (age) AND (allergy) AND (enrolled in the study) AND (fever) AND (greater than 16 years) AND (hypersensitivity) AND (less than 4 years) AND (liver disease) AND (morphine) AND (not) AND (pain score) AND (renal disease) AND (requiring) AND (within the past 4 hours) AND (within the past 72 hours))"}
{"candidate_id": "LLM03022", "doc_id": "NCT01567605_exc", "case_bucket": "or", "source_criterion": "cauda equina or conus lesion currently use ventilator colostomy, or do not perform regular bowel care for any reason any skin breakdown (pressure sores) do not speak English are under 19 years old are pregnant or think you might be pregnant medical/psychiatric condition or substance abuse that is likely to affect your ability to complete this study currently using medications containing lidocaine allergy to lidocaine", "candidate_expression": "((allergy) AND (currently) AND (do not perform) AND (lesion) AND (lidocaine) AND (medications containing lidocaine) AND (not) AND (old) AND (pressure sores) AND (skin breakdown) AND (speak English) AND (think you might be) AND (under 19 years) AND (ventilator) AND ((cauda equina) OR (conus)) AND ((pregnant)) AND ((medical condition) OR (psychiatric condition) OR (substance abuse)) AND ((colostomy) OR (regular bowel care)))"}
{"candidate_id": "LLM03023", "doc_id": "NCT02035800_exc", "case_bucket": "other", "source_criterion": "Patients not capable or willing to provide informed consent Patients starting Adalimumab less than five half-lives after the interruption of a previous anti-TNF therapy.", "candidate_expression": "((Adalimumab) AND (anti-TNF therapy) AND (less than five half-lives after the interruption of a previous anti-TNF therapy) AND (previous) AND (the interruption of a previous anti-TNF therapy))"}
{"candidate_id": "LLM03024", "doc_id": "NCT02774317_inc", "case_bucket": "or", "source_criterion": "Nonsurgical neonates and babies up to age 6 months with INR 1.5 or more who are deemed clinically to need plasma infusion.", "candidate_expression": "((INR 1.5 or more) AND (Nonsurgical) AND (age up to age 6 months) AND (babies) AND (need) AND (neonates) AND (plasma infusion))"}
{"candidate_id": "LLM03025", "doc_id": "NCT02339844_inc", "case_bucket": "or", "source_criterion": "Inclusion Criteria Patients: Fulfilling the diagnostic criteria of schizophrenia or schizoaffective disorder according to ICD-10 (International Classification of Diseases version 10) or DSM-IV/V (Diagnostic and Statistical Manual version 4 /5), Age 18-45 years, Never treated with antipsychotic compounds or central nervous system (CNS) stimulants, Legally competent Inclusion criteria controls: Matching patients on age (+/- 2 years), sex and parental socioeconomic status, Age 18-45 years, No psychiatric or physical disease.", "candidate_expression": "((18-45 years) AND (Age) AND (Legally competent) AND (Never) AND (No) AND (Patients) AND (antipsychotic compounds) AND (central nervous system (CNS) stimulants) AND (controls) AND ((physical disease) OR (psychiatric disease)) AND ((schizoaffective disorder) OR (schizophrenia)) AND ((DSM-IV/V (Diagnostic and Statistical Manual version 4 /5)) OR (ICD-10 (International Classification of Diseases version 10))))"}
```
