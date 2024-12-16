import os
import re
from tqdm import tqdm
import json
import pickle
import itertools
import numpy as np
from scipy.sparse import lil_matrix


class create_cooc:

    def __init__(self,
                 var,
                 year_var,
                 collection_name,
                 sub_var=None,
                 time_window=None,
                 dtype=np.uint32,
                 weighted_network=False,
                 self_loop=False):
        self.x = None
        self.item_list = {}
        self.var = var
        self.sub_var = sub_var
        self.year_var = year_var
        self.collection_name = collection_name
        self.dtype = dtype
        self.weighted_network = weighted_network
        self.self_loop = self_loop
        self.combinations = []

        type1 = 'weighted_network' if self.weighted_network else 'unweighted_network'
        type2 = 'self_loop' if self.self_loop else 'no_self_loop'

        self.collection_name = collection_name
        self.path_input = "../../Data/docs/{}".format(self.collection_name)
        self.path_output = "../../Data/cooc_sec/{}/{}_{}/fast_uzzi_sec/".format(var, type1, type2)

        if not os.path.exists(self.path_output):
            os.makedirs(self.path_output)

        if time_window:
            self.time_window = time_window
        else:
            self.time_window = [int(re.sub('.json', '', file)) for file in
                                os.listdir(self.path_input)]

    def get_item_list(self, docs, file, year):
        item_lists = {}
        for doc in docs:
            try:
                items = doc[self.var]
            except:
                continue

            item_names = []
            if self.sub_var is not None:
                for item in items:
                    refer_journal_name = item[self.sub_var]
                    if type(refer_journal_name) != str:
                        continue
                    item_names.append(refer_journal_name)

                    if refer_journal_name in item_lists:
                        continue
                    else:
                        item_lists[refer_journal_name] = 1

                items = item_names

            if not self.weighted_network:
                self.combinations.extend(list(itertools.combinations(set(items), r=2)))
            else:
                self.combinations.extend(itertools.combinations(items, r=2))

        self.item_list[year] = list(item_lists.keys())
        self.create_save_index(year)
        pickle.dump(self.combinations, open(self.path_output + "/{}.p".format(year), "wb"))

    def create_save_index(self, year):
        name2index = {name: index for name, index in
                      zip(self.item_list[year], range(0, len(self.item_list[year]), 1))}
        pickle.dump(name2index, open(self.path_output + "/{}_name2index.p".format(year), "wb"))

    def populate_item_list(self):
        for file in tqdm(os.listdir(self.path_input)):
            year = int(re.sub(".json", "", file))
            with open(self.path_input + "/{}".format(file), 'r') as infile:
                docs = json.load(infile)
            self.combinations = []
            self.get_item_list(docs, file, year)

    def construct_matrix(self, combi):
        try:
            combi = sorted((self.name2index[combi[0]], self.name2index[combi[1]]))
            ind_1 = combi[0]
            ind_2 = combi[1]
            self.x[ind_1, ind_2] += 1
        except:
            pass

    def main(self):
        self.populate_item_list()

        for year in tqdm(self.time_window):
            self.x = lil_matrix((len(self.item_list[year]), len(self.item_list[year])), dtype=self.dtype)
            self.combinations = pickle.load(open(self.path_output + "/{}.p".format(year), "rb"))
            with open(self.path_output + "/{}_name2index.p".format(year), "rb") as f:
                self.name2index = pickle.load(f)

            # 可以用多进程加速
            # 但python多进程某些情况下只作用于主函数中
            for object in self.combinations:
                self.construct_matrix(object)

            if not self.self_loop:
                self.x.setdiag(0)

            pickle.dump(self.x.tocsr(), open(self.path_output + "/{}.p".format(year), "wb"))
