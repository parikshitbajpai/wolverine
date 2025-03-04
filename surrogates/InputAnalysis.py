#%%
%matplotlib ipympl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

file = '../data/FeCr/generated_data.csv'
#%%
df = pd.read_csv(file)
df['TEMPERATURE']=df['TEMPERATURE'].astype('float64')
# %%
df.keys()
# %%
df.head()
# %%
df.tail()
# %%
df.shape
# %%
df.info()
# %%
df.describe()
# %%
plt.hist(df['G(LIQUID)'])
plt.show()
# %%
