import threading
import os
from tqdm import tqdm
from lxml import etree
import json

set_terms = set()
year_to_datas = []
pub_to_year = {}
specific_year = 2003
doi_to_name = {}
name_to_doi = {}


def load_data():
    with open("../../data/mesh/desc_simple.json", "r") as f:
        meshs_tree = json.load(f)

    desc_lists = list(meshs_tree.keys())
    term_texts = []
    for ui in desc_lists:
        concepts = meshs_tree[ui]['concept']
        for concept in concepts:
            term_texts.extend(concept['term'])

    return set(term_texts)


def get_mesh_terms(file, path):
    target_name = file.split('.')[-3] + "." + file.split('.')[-2]
    if not os.path.exists('../../data/plos_mesh/{}.json'.format(target_name)):
        tree = etree.parse(os.path.join(path, file))
        root = tree.getroot()

        sections, matches = [], []
        try:
            body = root.xpath('//body')[0]
            num_sections = len(body)

            if num_sections > 0:
                for sec in body:
                    try:
                        sec_matches = []
                        title = sec[0]
                        sec_name = title.text
                        p_list = sec.xpath(".//p")
                        for p in p_list:
                            p_content = etree.tostring(p).decode('utf-8')
                            paper_words = set(p_content.split())
                            found_mesh_words = paper_words.intersection(set_terms)
                            if len(found_mesh_words) > 0:
                                sec_matches.extend(found_mesh_words)
                                matches.extend(found_mesh_words)
                        sections.append({
                            'name': sec_name,
                            'refer': sec_matches
                        })
                    except:
                        print("The structure of {} is unstandard".format(file))
                        continue
            else:
                p_list = body.xpath(".//p")
                for p in p_list:
                    p_content = etree.tostring(p).decode('utf-8')
                    paper_words = set(p_content.split())
                    found_mesh_words = paper_words.intersection(set_terms)
                    if len(found_mesh_words) > 0:
                        matches.extend(found_mesh_words)

            metadata = {}
            dois = root.xpath("//article-id[@pub-id-type=\"doi\"]")
            for doi in dois:
                metadata['doi'] = doi.text
            metadata['doi'] = metadata['doi'].replace("\n", '').strip()
            metadata['mesh'] = matches
            metadata['section'] = sections

            json_metadata = json.dumps(metadata, indent=4)
            with open('../../data/plos_mesh/{}.json'.format(target_name), 'w') as f:
                f.write(json_metadata)
        except:
            pass


def organize_by_year(name):
    try:
        with open(os.path.join('../../data/plos_mesh', name), 'r') as f:
            metadata = json.load(f)

        # del metadata['title']
        # del metadata['abstract']
        del metadata['section']
        # del metadata['journal']

        year_to_datas.append(metadata)

    except Exception as e:
        print(f"{e}")


def organize_by_sec(name):
    with open(os.path.join('../../data/plos_mesh', name), 'r') as f:
        metadata = json.load(f)
    del metadata['mesh']

    try:
        doi = metadata['doi']
        sections = metadata['section']
        for idx, sec in enumerate(sections):
            sec_metadata = {}
            mesh = sec['refer']
            if len(mesh) == 0:
                continue
            sec_metadata['doi'] = doi + '_{}'.format(idx)
            sec_metadata['original_doi'] = doi
            sec_metadata['mesh'] = mesh
            sec_metadata['year'] = specific_year
            year_to_datas.append(sec_metadata)
    except:
        year_to_datas.append(metadata)


def get_sections(name):
    with open(os.path.join('../../data/plos_mesh', name), 'r') as f:
        metadata = json.load(f)

    try:
        doi = metadata['doi']
        sections = metadata['section']
        for idx, sec in enumerate(sections):
            sec_metadata = {}
            mesh = sec['refer']
            if len(mesh) == 0:

def get_doi_link_name(name):
    try:
        with open(os.path.join("../../data/plos_mesh", name), 'r') as file:
            metadata = json.load(file)

        doi = metadata['doi']
        doi_to_name[doi] = name
    except Exception as e:
        print(f"{e}")


def call_parse(path, names, part_name):
    for name in tqdm(names, desc=part_name):
        # get_mesh_terms(name, path)
        # organize_by_year(name)
        organize_by_sec(name)
        # get_doi_link_name(name)


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


def process_in_threads(file_dicts, path):
    threads = []

    for part_name in file_dicts.keys():
        thread = threading.Thread(target=call_parse, args=(path, file_dicts[part_name], part_name))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


def filter_filenames(old_names):
    new_pub_to_year = {}
    for doi in pub_to_year:
        years = pub_to_year[doi]
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
        except Exception as e:
            continue

    return new_names


if __name__ == "__main__":
    # 1. 获取每篇论文中的Mesh词
    # input_path = 'G:\\Dataset\\PLOS\\allofplos'
    # filenames = os.listdir(input_path)
    # set_terms = load_data()
    #
    # file_parts = split_filenames(filenames, 8)
    # process_in_threads(file_parts, input_path)

    input_path = "../../data/plos_mesh"
    filenames = os.listdir(input_path)

    # 2. 获取doi和文件名间的匹配关系
    # filename_parts = split_filenames(filenames, 10)
    # process_in_threads(filename_parts, input_path)
    #
    # doi_to_name = json.dumps(doi_to_name, indent=4)
    # with open('../Data/plos_mesh_doi_to_name.json', 'w') as f:
    #     f.write(doi_to_name)

    # 3. 将记录按照年份、章节进行组织
    with open("../../data/plos_pub_year.json", 'r') as f:
        pub_to_year = json.load(f)
    with open("../Data/plos_mesh_doi_to_name.json") as f:
        doi_to_name = json.load(f)
    name_to_doi = {v: k.strip() for k, v in doi_to_name.items()}

    for year in range(2003, 2025):
        specific_year = year
        filter_files = filter_filenames(filenames)
        file_parts = split_filenames(filter_files, 8)

        process_in_threads(file_parts, input_path)

        json_datas = json.dumps(year_to_datas, indent=4)

        with open("../Data/docs/sec_mesh_level/{}.json".format(str(specific_year)), 'w') as f:
            f.write(json_datas)

        year_to_datas = []
