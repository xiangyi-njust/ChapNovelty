import os
import json
import threading
from tqdm import tqdm

co_occurences = {}


def stat_co_occurence(journal_list):
    for idx_1, refer_1 in enumerate(journal_list[:-1]):
        if refer_1 not in co_occurences:
            co_occurences[refer_1] = {}
            # co_occurences[refer_1] = []
            for _, refer_2 in enumerate(journal_list[idx_1:]):
                if refer_1 == refer_2:
                    continue
                # co_occurences[refer_1].append(refer_2)
                if refer_2 in co_occurences[refer_1]:
                    co_occurences[refer_1][refer_2] += 1
                else:
                    co_occurences[refer_1][refer_2] = 1


def get_combination(file, mode='sec'):
    with open(os.path.join("../data/plos", file), 'r') as f:
        metadata = json.load(f)

    refer_items = metadata['reference']

    refer_ids, refer_journals = [], []

    for item in refer_items:
        refer_ids.append(item['id'])
        refer_journals.append(item['source'])

    if mode == 'sec':
        id_to_journal = {id: journal for id, journal in zip(refer_ids, refer_journals)}

        sec_items = metadata['section']
        for sec in sec_items:
            sec_id = sec['refer']
            sec_refer = [id_to_journal[id] for id in sec_id]
            stat_co_occurence(list(set(sec_refer)))
    else:
        stat_co_occurence(list(set(refer_journals)))


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


def call_parse(names, part_name):
    for name in tqdm(names, desc=part_name):
        get_combination(name)


def process_in_threads(file_dicts):
    threads = []

    for part_name in file_dicts.keys():
        thread = threading.Thread(target=call_parse, args=(file_dicts[part_name], part_name))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


def get_file_names(pub_to_year, doi_to_name, target_year):
    reserve_dois = []

    for doi, years in zip(pub_to_year.keys(), pub_to_year.values()):
        year = 0
        try:
            year = int(years['ppub'])
        except:
            year = int(years['epub'])

        if year < target_year:
            reserve_dois.append(doi)

    reserve_names = []
    all_filenames = os.listdir("../data/plos/")
    for doi in reserve_dois:
        doi = doi.replace('\n', '').strip()
        try:
            reserve_names.append(doi_to_name[doi])
        except:
            try:
                simple_name = doi.split('.')[-3] + '.' + doi.split('.')[-2] + ".json"
                if simple_name in all_filenames:
                    reserve_names.append(simple_name)
                    continue

                other_simple_name = doi.split('.')[-2] + '.' + doi.split('.')[-1] + ".json"
                if other_simple_name in all_filenames:
                    reserve_names.append(other_simple_name)
                    continue
            except:
                print(doi)
                continue

    return reserve_names


if __name__ == '__main__':
    with open("../data/plos_pub_year.json", 'r') as f:
        pub_to_year = json.load(f)

    with open("../data/plos_doi_to_name.json", "r") as f:
        doi_to_name = json.load(f)

    filenames = get_file_names(pub_to_year, doi_to_name, 2012)
    filename_parts = split_filenames(filenames, 10)
    process_in_threads(filename_parts)

    print(len(list(co_occurences.keys())))

    co_occurences = json.dumps(co_occurences, indent=4)
    with open('test2003.json', 'w') as f:
        f.write(co_occurences)
