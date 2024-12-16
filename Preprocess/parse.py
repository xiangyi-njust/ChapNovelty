from tqdm import tqdm
import os
from lxml import etree
import json
import threading

# for parse_author_and_aff
doi_to_datas = {}

def parse_section_name(root, filename):
    section_names = []
    tag_names = []

    body = root.xpath('//body')[0]
    num_sections = len(body)

    if num_sections > 0:
        for sec in body:
            try:
                title = sec[0]
                section_names.append(title.text)
                tag_names.append(sec.tag)
            except:
                print("The structure of {} is unstandard".format(filename))
                break

    return section_names, tag_names


def parse_metadata(root):
    metadata = {}

    dois = root.xpath("//article-id[@pub-id-type=\"doi\"]")
    for doi in dois:
        metadata['doi'] = doi.text

    journal_titles = root.xpath("//journal-meta//journal-title")
    metadata['journal'] = ''
    for title in journal_titles:
        metadata['journal'] = title.text

    paper_titles = root.xpath("//article-meta//article-title")
    metadata['title'] = []
    for title in paper_titles:
        metadata['title'].append(title.text)

    abstracts = root.xpath("//article-meta//abstract")
    metadata['abstract'] = []
    for abstract in abstracts:
        metadata['abstract'].append(abstract[0].text)

    return metadata


def parse_reference(root):
    references = []
    refer_list = root.xpath("//back//ref")
    for refer in refer_list:
        refer_structure = {}
        id = refer.attrib['id']
        refer_structure['id'] = id
        try:
            refer_structure['title'] = refer.xpath("//ref[@id=\"{}\"]//article-title".format(id))[0].text
        except:
            refer_structure['title'] = ''
        try:
            refer_structure['source'] = refer.xpath("//ref[@id=\"{}\"]//source".format(id))[0].text
        except:
            refer_structure['source'] = ''
        try:
            refer_structure['year'] = refer.xpath("//ref[@id=\"{}\"]//year".format(id))[0].text
        except:
            refer_structure['year'] = ''
        try:
            publication_type = refer.xpath(".//nlm-citation")
            refer_structure['publication-type'] = publication_type[0].attrib['publication-type']
        except:
            refer_structure['year'] = ''
        references.append(refer_structure)

    return references


def parse_content(root, filename, references):
    sections = []

    body = root.xpath('//body')[0]
    num_sections = len(body)

    if num_sections > 0:
        for sec in body:
            try:
                title = sec[0]
                sec_name = title.text
                refer_lists = []
                p_list = sec.xpath(".//p")
                for p in p_list:
                    sec_content = etree.tostring(p).decode('utf-8')
                    for refer in references:
                        if refer in sec_content:
                            refer_lists.append(refer)
                sections.append({
                    'name': sec_name,
                    'refer': refer_lists
                })
            except:
                print("The structure of {} is unstandard".format(filename))
                break

    return sections


def parse_file(path, filename):
    target_name = filename.split('.')[-3] + "." + filename.split('.')[-2]
    target_file = os.path.join("../../data/plos", target_name + '.json')

    tree = etree.parse(os.path.join(path, filename))
    root = tree.getroot()
    
    if not os.path.exists(target_file):
        metadata = parse_metadata(root)
        references = parse_reference(root)

        metadata['reference'] = references

        reference_ids = [reference['id'] for reference in references]
        sections = parse_content(root, filename, reference_ids)
        metadata['section'] = sections
    else:
        # 如果存在，意味着只需进行部分修改
        with open(target_file, 'r') as f:
            metadata = json.load(f)
        
        # 2024/9/13 修改章节识别结果，并添加参考文献类型信息        
        references = parse_reference(root)
        reference_ids = [reference['id'] for reference in references]
        sections = parse_content(root, filename, reference_ids)
        metadata['section'] = sections
        metadata['reference'] = references

    json_metadata = json.dumps(metadata, indent=4)
    with open(target_file, 'w') as f:
        f.write(json_metadata)


def parse_author_and_aff(path, filename):
    try:
        tree = etree.parse(os.path.join(path, filename))
        authors = tree.xpath("//contrib[@contrib-type=\"author\"]")
        affs = tree.xpath("//aff[contains(@id, 'aff')]")

        file = '10.1371/' + filename[filename.find("journal"):-4]
        doi_to_datas[file] = {
            'author': len(authors),
            'aff': len(affs)
        }
    except Exception as e:
        pass


def parse_year(root):
    paper_doi = ''
    dois = root.xpath("//article-id[@pub-id-type=\"doi\"]")
    for doi in dois:
        paper_doi = doi.text

    pub_dates = {}

    items = root.xpath("//pub-date")
    for item in items:
        try:
            pub_dates[item.attrib['pub-type']] = item.xpath("//year")[0].text
        except:
            continue

    return pub_dates, paper_doi

    
def call_parse(path, names, part_name):
    for name in tqdm(names, desc=part_name):
        # parse_file(path, name)
        parse_author_and_aff(path, name)


def split_filenames(files, k):
    file_parts = {}
    part_length = int(len(files)/k)
    for i in range(k+1):
        part_name = 'part_{}'.format(i)
        if (i+1)*part_length > len(files):
            part_files = files[i*part_length:]
        else:
            part_files = files[i*part_length:(i+1)*part_length]
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


if __name__ == '__main__':
    filepath = "G:\\Dataset\\PLOS\\allofplos"
    filenames = os.listdir(filepath)

    # 1.1 parse main content
    filename_parts = split_filenames(filenames, 10)

    process_in_threads(filename_parts, filepath)

    # 1.2 parse paper publication year
    # paper_to_year = {}
    # for filename in tqdm(filenames):
    #     try:
    #         tree = etree.parse(os.path.join(filepath, filename))
    #         root = tree.getroot()
    #         pub_dates, paper_doi = parse_year(root)
    #         paper_to_year[paper_doi] = pub_dates
    #     except:
    #         print(filename)

    # paper_to_year = json.dumps(paper_to_year, indent=4)
    # with open('../data/plos/plos_pub_year.json', 'w') as f:
    #     f.write(paper_to_year)

    # 1.3 parse author and affiliation
    doi_to_datas = json.dumps(doi_to_datas, indent=4)
    with open("../../data/plos_author_aff.json", 'w') as f:
        f.write(doi_to_datas)