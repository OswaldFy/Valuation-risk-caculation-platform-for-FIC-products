import pandas as pd
import numpy as np
import datetime

def import_data(path):

    _data = {}

    main_df = pd.read_excel(path, sheet_name='main')
    main = {'valuation date': pd.Timestamp(datetime.date(2023, 3, 31)), 'data': main_df}

    _data['main'] = main

    cs_df = pd.read_excel(path, sheet_name='cs')
    cs = {'name': 'CAD_3M AAA_31-Mar-2023', 'valuation date': pd.Timestamp(datetime.date(2023, 3, 31)), 'currency': 'CAD', 'data': cs_df}

    _data['cs'] = cs
    
    
    cs_all_df = pd.read_excel(path, sheet_name='cs_all')
    cs_all = {'valuation date': pd.Timestamp(datetime.date(2023, 3, 31)), 'currency': 'CAD', 'data': cs_all_df}

    _data['cs_all'] = cs_all

    ir_df = pd.read_excel(path, sheet_name='ir')
    ir = {'name': 'CAD_3M Libor_31-Mar-2023', 'valuation date': pd.Timestamp(datetime.date(2023, 3, 31)), 'currency': 'CAD', 'data': ir_df}

    _data['ir'] = ir

    return _data