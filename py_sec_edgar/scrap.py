import pandas as pd
import numpy as np

file = r'C:\@PROJECTS\py-sec-edgar\refdata\merged_idx_files.csv'

df_idx = pd.read_csv(file, index_col=0, dtype={"CIK": int})

df_idx['CIK'].nunique()
# 642,927

df_idx['Form Type'].nunique()
# 679

df_forms = df_idx.groupby(['Form Type']).size().to_frame('Form Type').sort_values('Form Type', ascending=False)




df_idx['Form Type'].str.contains("10-K")
