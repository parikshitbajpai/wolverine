# # %matplotlib ipympl
# # import matplotlib.pyplot as plt
# # import numpy  as np
import pandas as pd
import glob
import argparse
import sys
import numpy as np

#
# Parameters
#

# cmd = ' '.join(sys.argv)
# parser = argparse.ArgumentParser(description='Generate single datafile from multiple datafiles.')
# parser.add_argument('output')



file_pattern = 'data/FeCr/T*.dat'
files = glob.glob(file_pattern)
print(files)

num_header_lines = 6
num_footer_lines = 8
delimiter_pattern = r'\s+|,'
column_names = [
    'X(CR)', 'G(FCC_A1)', 'G(BCC_A2)', 'G(LIQUID)', 'M(FCC_A1,CR)', 'M(FCC_A1,FE)',
    'M(BCC_A2,CR)', 'M(BCC_A2,FE)', 'M(LIQUID,CR)', 'M(LIQUID,FE)', 'MU(CR)', 'MU(FE)',
    'MUR(CR,FCC_A1)', 'MUR(FE,FCC_A1)', 'MUR(CR,BCC_A2)', 'MUR(FE,BCC_A2)', 'MUR(CR,LIQUID)',
    'MUR(FE,LIQUID)', 'TEMPERATURE'
]

input_cols = ['X(CR)', 'TEMPERATURE']
output_cols = ['G(FCC_A1)', 'G(BCC_A2)', 'G(LIQUID)']

dataframes = []
for file in files:
  df = pd.read_csv(file, sep=delimiter_pattern, skiprows=num_header_lines, skipfooter=num_footer_lines, engine='python', names=column_names)

  temperature = int(file.split('T')[1].split('.')[0])
  df['TEMPERATURE'] = temperature

  dataframes.append(df)

dataframe = pd.concat(dataframes,ignore_index=True)
print(len(dataframe))

# Reorder columns to make 'TEMPERATURE' the second column
# dataframe = dataframe[['TEMPERATURE'] + [col for col in dataframe.columns if col!= 'TEMPERATURE']]
dataframe = dataframe[[col for col in input_cols] + [col for col in output_cols]]


train_len = int(len(dataframe) * 0.666)
choice = np.random.choice(range(len(dataframe)), size=(train_len,), replace=False)
print(choice.shape)
train_idx = np.zeros(len(dataframe), dtype=bool)
print(choice.shape)
train_idx[choice] = True
print(choice.shape)
dataframe_out  = dataframe[train_idx]


# dataframe.to_csv('data/FeCr/new_truncated_generated_data.csv',index=False)
# dataframe_out.to_csv('data/FeCr/truncated_generated_data.txt', sep=' ', index=False)


# import pandas as pd
# import glob
# import re
# from pathlib import Path

# # Define file pattern and column names
# file_pattern = Path('data/FeCr') / 'T*.dat'
# column_names = [
#   'X(CR)', 'G(FCC_A1)', 'G(BCC_A2)', 'G(LIQUID)', 'M(FCC_A1,CR)', 'M(FCC_A1,FE)',
#   'M(BCC_A2,CR)', 'M(BCC_A2,FE)', 'M(LIQUID,CR)', 'M(LIQUID,FE)', 'MU(CR)', 'MU(FE)',
#   'MUR(CR,FCC_A1)', 'MUR(FE,FCC_A1)', 'MUR(CR,BCC_A2)', 'MUR(FE,BCC_A2)', 'MUR(CR,LIQUID)',
#   'MUR(FE,LIQUID)', 'TEMPERATURE'
# ]

# # Define regex pattern for delimiter and number of header and footer lines
# delimiter_pattern = re.compile(r'\s+|,')
# num_header_lines = 6
# num_footer_lines = 8

# # Find all matching files and process them
# dataframes = []
# for file in file_pattern.glob('*'):
#   # Read CSV data with specified parameters
#   df = pd.read_csv(
#     file,
#     sep=delimiter_pattern,
#     skiprows=num_header_lines,
#     skipfooter=num_footer_lines,
#     engine='python',
#     names=column_names
#     )

#   # Extract temperature from the filename and add it as a new column
#   temperature = int(file.stem.split('T')[1])
#   df['TEMPERATURE'] = temperature

#   dataframes.append(df)

# print(dataframes)

# # Concatenate all dataframes into one and reset index
# dataframe = pd.concat(dataframes, ignore_index=True)

# # Reorder columns to make 'TEMPERATURE' the second column
# dataframe = dataframe[['TEMPERATURE'] + [col for col in dataframe.columns if col!= 'TEMPERATURE']]

# # Save the resulting dataframe to a CSV file
# dataframe.to_csv('data/FeCr/generated_data_2.csv', index=False)
