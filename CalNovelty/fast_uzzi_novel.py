from lib.fastnovelpy.indicators import *
# from novelpy.indicators import *


if __name__ == '__main__':
    for year in range(2021, 2025):
        uzzi_novelty = Uzzi2013(collection_name='sec_level_nomarlize_remove_unmatch',
                                id_variable='doi',
                                year_variable='year',
                                variable='reference',
                                focal_year=year,
                                sub_variable='source',
                                density=True)

        uzzi_novelty.get_indicator()
