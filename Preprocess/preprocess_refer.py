import threading
from tqdm import tqdm
import os
import json

doi_to_name = {}
pub_to_year = {}
all_sections = []
miss_section_dois = []

"""
    year_to_datas: 存储每一年数据的json文件
    year_sec_to_datas: 存储每一年数据的json文件，原始文件按照参考文献在段落中的共现关系重新组织
    sec_metadata: 存储按章节存储后的文件名之前对应的具体章节名
"""
year_to_datas = []
specific_year = 2004
name_to_doi = {}
sec_metadata = {}

"""
    2024/9/5: 获取section数据，并构建doi和文件名之间的匹配关系
"""


# def get_sections(name):
#     with open(os.path.join('../data/plos', name), 'r') as f:
#         metadata = json.load(f)

#     doi = metadata['doi']
#     doi_to_name[doi] = name
#     sections = [item['name'] for item in metadata['section']]
#     if len(sections) == 0:
#         miss_section_dois.append(doi)
#     else:
#         all_sections.extend(sections)


def split_filenames(files, k):
    file_parts = {}
    part_length = int(len(files) / k)
    for i in range(k + 1):
        part_name = 'part_{}'.format(i)
        if (i + 1) * part_length > len(files):
            part_files = files[i * part_length:]
        else:
            part_files = files[i * part_length:(i + 1) * part_length]
        file_parts[part_name] = part_files

    return file_parts


"""
    2024/9/6: 在metadata中添加year字段，方便使用novelpy进行新颖性预测
    添加函数：
            add_year: 根据parse中得到的pub_to_year文件将year字段添加到原始数据中
            orginize_by_year: novelypy要求将每年的数据组织在一个文件中
"""


def add_year(name):
    with open(os.path.join('../data/plos', name), 'r') as f:
        metadata = json.load(f)

    doi = metadata['doi']
    # 找不到年份的论文相当于在计算新颖性的时候不纳入考虑，给一个目前不存在的年份
    metadata['year'] = 2030
    try:
        years = pub_to_year[doi]
        year = 0
        try:
            year = int(years['ppub'])
        except:
            year = int(years['epub'])
        metadata['year'] = year
    except:
        print(doi)

    json_metadata = json.dumps(metadata, indent=4)
    with open(os.path.join('../data/plos', name), 'w') as f:
        f.write(json_metadata)


def organize_by_year(name):
    try:
        with open(os.path.join('../../data/plos', name), 'r') as f:
            metadata = json.load(f)
        if metadata['year'] == specific_year:
            del metadata['title']
            del metadata['abstract']
            del metadata['section']
            del metadata['journal']

            year_to_datas.append(metadata)
    except:
        pass


def organize_by_sec(name):
    with open(os.path.join("../../data/plos", name), 'r') as file:
        metadata = json.load(file)
    # if metadata['year'] == specific_year:
    del metadata['title']
    del metadata['abstract']
    del metadata['journal']

    try:
        sections = metadata['section']
        references = metadata['reference']
        refer_id_dict = {refer['id']: refer for refer in references}
        for idx, sec in enumerate(sections):
            try:
                sec_refer_id_list = sec['refer']
                sec_metadata = {}
                sec_refer = []
                for refer_id in sec_refer_id_list:
                    try:
                        sec_refer.append(refer_id_dict[refer_id])
                    except:
                        continue
                if len(sec_refer) == 0:
                    continue
                sec_metadata['doi'] = metadata['doi'] + '_{}'.format(idx)
                sec_metadata['original_doi'] = metadata['doi']
                sec_metadata['reference'] = sec_refer
                sec_metadata['year'] = specific_year
                year_to_datas.append(sec_metadata)
            except:
                continue
    except:
        year_to_datas.append(metadata)


def get_sections(name):
    with open(os.path.join('../../data/plos', name), 'r') as f:
        metadata = json.load(f)
    
    del metadata['title']
    del metadata['abstract']
    del metadata['journal']
    del metadata['reference']

    try:
        sections = metadata['section']
        for idx, sec in enumerate(sections):
            try:
                sec_name = sec['name']
                sec_metadata[metadata['doi'] + '_{}'.format(idx)] = sec_name
            except:
                continue
    except:
        pass



def get_doi_link_name(name):
    try:
        with open(os.path.join("../../data/plos", name), 'r') as file:
            metadata = json.load(file)

        doi = metadata['doi']
        doi_to_name[doi] = name
    except:
        pass


def call_parse(names, part_name):
    for name in tqdm(names, desc=part_name):
        # get_doi_link_name(name)
        get_sections(name)
        # add_year(name)
        # organize_by_year(name)
        # organize_by_sec(name)


def process_in_threads(file_dicts):
    threads = []

    for part_name in file_dicts.keys():
        thread = threading.Thread(target=call_parse, args=(file_dicts[part_name], part_name))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


def filter_filenames(old_names):
    with open("../../data/plos_pub_year.json") as f:
        old_pub_to_year = json.load(f)
    with open("../Data/plos_refer_doi_to_name.json") as f:
        doi_to_name = json.load(f)

    name_to_doi = {v: k.strip() for k, v in doi_to_name.items()}
    new_pub_to_year = {}
    for doi in old_pub_to_year:
        years = old_pub_to_year[doi]
        year = 0
        try:
            year = int(years['ppub'])
        except:
            year = int(years['epub'])
        new_pub_to_year[doi.strip()] = year

    new_names = []
    for name in old_names:
        try:
            if new_pub_to_year[name_to_doi[name]] == specific_year:
                new_names.append(name)
        except:
            continue

    return new_names


if __name__ == '__main__':
    filepath = "../../data/plos"
    filenames = os.listdir(filepath)

    # 1. 预处理得到doi和文件名之间的对应关系
    # filename_parts = split_filenames(filenames, 10)
    # process_in_threads(filename_parts)

    # doi_to_name = json.dumps(doi_to_name, indent=4)
    # with open('../data/plos_refer_doi_to_name.json', 'w') as f:
    #     f.write(doi_to_name)

    # 2. 在原始数据中添加year字段
    # with open("../data/plos_pub_year.json", 'r') as f:
    #     pub_to_year = json.load(f)

    # process_in_threads(filename_parts)

    # 3. 将数据按年份存储  代码分年份处理，防止一次性存入过多的数据在内存中
    # 相当于以时间换空间，针对每一个年份单独运行一次代码
    # for year in tqdm(range(2014, 2025)):
    #     specific_year = year
    #     filter_files = filter_filenames(filenames)
    #     file_parts = split_filenames(filter_files, 10)
    #     process_in_threads(file_parts)

    #     json_datas = json.dumps(year_to_datas, indent=4)
    #     with open("../Data/docs/sec_level/{}.json".format(str(specific_year)), 'w') as f:
    #         f.write(json_datas)
        
    #     year_to_datas = []

    # 4. 获取按sec存储过后的文件名与其原先的章节名之间的对应关系
    for year in tqdm(range(2003, 2025)):
        specific_year = year
        filter_files = filter_filenames(filenames)
        file_parts = split_filenames(filter_files, 10)
        process_in_threads(file_parts)

    json_datas = json.dumps(sec_metadata, indent=4)
    with open('../Data/docs/sec_level/sec_to_name.json', 'w') as f:
        f.write(json_datas)