This is the code of this paper "Quantifying Novelty in Scientific Research Paper: A Logistical Structure-Based Approach"

<details>
<summary> <h3> Project Structure  </h3> </summary>
'''plaintext
ChapNovelty
├─ Analyse
│    ├─ EDA.ipynb
│    ├─ Preprocess.ipynb
│    ├─ RobustCheck.ipynb
│    ├─ Validate.ipynb
│    ├─ base_data
│    │    ├─ compare_sec
│    │    ├─ compare_specific_sec
│    │    └─ overview
│    ├─ gold_standard
│    │    ├─ F1000
│    │    └─ regression
│    ├─ log
│    ├─ robust
│    │    ├─ log-extra-control-variable
│    │    ├─ log-just-outlier
│    │    └─ outliers
├─ CalNovelty
│    ├─ cal_novelty.ipynb
│    ├─ construct_cooc.py
│    ├─ fast_uzzi_novel.py
│    ├─ lib
│    │    ├─ __init__.py
│    │    └─ fastnovelpy
│    ├─ norm_sec.ipynb
│    ├─ npy_wang_novel.py
│    ├─ self_refer_novelty.py
│    └─ self_wang_novel.py
├─ Preprocess
│    ├─ EDA_mesh.ipynb
│    ├─ EDA_plos.ipynb
│    ├─ cal_distance.py
│    ├─ crawl_abbr.py
│    ├─ data
│    │    ├─ close_form_journal.csv
│    │    ├─ close_form_journal.json
│    │    └─ standard_journals.csv
│    ├─ filter_file.py
│    ├─ get_refer_name.py
│    ├─ norm_refer.py
│    ├─ norm_refer_check.py
│    ├─ norm_sec.ipynb
│    ├─ optim_sec_and_refer_name.ipynb
│    ├─ parse.py
│    ├─ preprocess_mesh.py
│    └─ preprocess_refer.py
└─ readme.MD
</details>
