from pandas import pandas as pd
import json
import datetime


def parser(data):
    try:
        pd.read_json(json.dumps(data)).to_csv("%s.csv" % (datetime.datetime.now().strftime("%H:%M:%S.%F")))
        return
    except Exception as e:
        raise e
