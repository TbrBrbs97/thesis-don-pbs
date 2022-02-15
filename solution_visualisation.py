import pandas as pd


def convert_to_dataframe(dictionairy):

    df = pd.DataFrame.from_dict({(i, j): dictionairy[i][j]
                           for i in dictionairy.keys()
                           for j in dictionairy[i].keys()},
                       orient='index')
    return df

