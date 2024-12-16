import pandas as pd
import json
import os
from tqdm import tqdm
import re

word_to_close_form = {}

def load_data():
    unstand_to_stand = {}

    with open("data/abbreviation.json", "r") as f:
        res_dict = json.load(f)

    with open("data/abbreviation_nlm.json", 'r') as f:
        nlm_res_dict = json.load(f)

    for res in nlm_res_dict:
        if nlm_res_dict[res] is not None:
            for value in nlm_res_dict[res]:
                unstand_to_stand[value] = res
            unstand_to_stand[res] = res
    
    for res in res_dict:
        if res_dict[res] is not None:
            for value in res_dict[res]:
                unstand_to_stand[value] = res
            unstand_to_stand[res] = res

    with open("data/close_form_journal.json", "r") as f:
        word_to_close_form = json.load(f)

    return unstand_to_stand


def normalize(in_path, out_path, year, nomarlize_dict):
    """
        判断逻辑：
         1. 首先看当前期刊名是否在字典中出现过，如果出现直接匹配，如果不出现进行第二步
         2. 查看与该期刊名最相近的期刊名，检查其是否在字典中出现
    """
    if os.path.exists(os.path.join(out_path, "{}.json".format(year))):
        return None

    in_path = os.path.join(in_path, "{}.json".format(year))
    with open(in_path, "r") as f:
        datas = json.load(f)

    norm_datas = []
    for paper_data in tqdm(datas):
        old_references = paper_data["reference"]
        norm_references = []
        for refer in old_references:
            refer_source = refer['source']
            
            # normalize
            if type(refer_source) is not str:
                continue
            if "rxiv" in refer_source.lower():
                continue
            if refer_source.count(".") == 1:
                refer_source = refer_source[:refer_source.find(".")]
            if refer_source.count(":") == 1:
                refer_source = refer_source[:refer_source.find(":")]
            refer_source.replace("&", "and")
            refer_source = re.sub(r'\.|\(.*?\)|\"', '', refer_source)
            
            flag = False
            if refer_source not in nomarlize_dict:
                if refer_source in word_to_close_form and len(word_to_close_form[refer_source]) != 0:
                    close_forms = word_to_close_form[refer_source]
                    for form in close_forms:
                        if form in nomarlize_dict:
                            refer['source'] = nomarlize_dict[form]
                            norm_references.append(refer)
                            flag = True
                            break
            else:
                refer['source'] = nomarlize_dict[refer_source]
                norm_references.append(refer)
                flag = True

            # 如果找不到匹配的，则去除该参考文献
            if not flag:
                continue
        
        # 如果参考文献列表为空，则去除该数据
        if len(norm_references) == 0:
            continue

        paper_data["reference"] = norm_references
        norm_datas.append(paper_data)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    norm_datas = json.dumps(norm_datas, indent=4)
    with open(os.path.join(out_path, "{}.json".format(year)), "w") as f:
        f.write(norm_datas)


if __name__ == '__main__':
    nomarlize_dict = load_data()

    input_path = "../Data/docs/sec_level"
    output_path = "../Data/docs/sec_level_nomarlize_remove_unmatch"

    for year in tqdm(range(2003, 2025)):
        normalize(input_path, output_path, year, nomarlize_dict)
