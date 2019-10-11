#******************************************************************************************************************************************
# TITLE     : ROUTINE_GET_HISTOGRAM
# AUTHOR    : PRAKASH HIREMATH M
# DATE      : AUG 2018 - JUN 2019
# INSTITUTE : INDIAN INSTITUTE OF SCIENCE
#******************************************************************************************************************************************


#******************************************************************************************************************************************
# VERSION HISTORY
#******************************************************************************************************************************************
# DATE (YYYY-MM-DD) | AUTHOR              | COMMENTS
#------------------------------------------------------------------------------------------------------------------------------------------
# 2019-10-11        | PRAKASH HIREMATH M  | Initial version
#******************************************************************************************************************************************

import pandas as pd
import numpy as np
import datetime

from matplotlib import pyplot as plt

#==============================================================================================

#Procedure to obtain histogram of the data (pandas series or numpy array) with given precision
print('Start of defining procedure : get_mode_df :', datetime.datetime.now())
print('Version : 2019-04-23 12:50')

def get_mode_df(pcb_data_df,THRESHOLD,HISTBIN_WINDOW):
    mode_df = pd.DataFrame(columns=['str_index','end_index','local_mode'])

    LOCAL_STR_FLAG = 1

    for i in range(1,len(pcb_data_df)):
        if (LOCAL_STR_FLAG == 1):
            str_index = pcb_data_df.arvl_index[i-1]
            local_str = i-1
            LOCAL_STR_FLAG = 0
            print('str_index =', str_index)
            print('local_str =', local_str)
        #end-if
    
        samp_diff = pcb_data_df.arvl_index[i] - pcb_data_df.dptr_index[i-1]
    
        if ((i == len(pcb_data_df)-1) | (samp_diff >= THRESHOLD)): 
            if (i == len(pcb_data_df)-1): #last entry of dataframe
                end_index = pcb_data_df.dptr_index[i]
                local_end = i
            elif (samp_diff >= THRESHOLD):
                end_index = pcb_data_df.dptr_index[i-1]
                local_end = i-1
            #end-if
            LOCAL_STR_FLAG = 1
            print('end_index =', end_index)
            print('local_end =', local_end)
            pcb_srs = pcb_data_df
            hist_df,local_mode = get_mode(pcb_data_df.pcb_actv_dur[local_str:local_end+1],0,HISTBIN_WINDOW)
            print('local_mode =', local_mode)
            print('------------------------')
            data = pd.DataFrame([[str_index,end_index,local_mode]],columns=['str_index','end_index','local_mode'])
            mode_df = mode_df.append(data)
            del data
        #end-if    
    #end-for
    
    return mode_df

#end-proc
print('End   of defining procedure : get_mode_df :', datetime.datetime.now())

#--------------------------------------------
print('Start of defining procedure : get_mode :', datetime.datetime.now())
print('Version : 2019-05-27 21:28')

def get_mode(inp_srs,start,HISTBIN_WINDOW):
    hist_df = pd.DataFrame(columns=['start','end','no_occur'])
    while (start <= np.max(inp_srs)):
        end = start + HISTBIN_WINDOW
        no_occur = np.sum((inp_srs >= start) & (inp_srs < end))
        data = pd.DataFrame([[start,end,no_occur]],columns=['start','end','no_occur'])
        hist_df = hist_df.append(data)
        del data
        start = end
    #end-while   

    hist_df = hist_df.reset_index()
    hist_df = hist_df.iloc[:,1:len(hist_df.columns)]

    plt.figure(figsize=(18,6));
    plt.stem(hist_df.start,hist_df.no_occur); plt.grid();
    plt.xlabel('Start of bin'); plt.ylabel('Occurences');
    
    MAX_OCCUR = hist_df.no_occur.max()
    a = hist_df.index[hist_df.no_occur == MAX_OCCUR]
    max_ind = np.asscalar(a[0])
    mode = (hist_df.start[max_ind] + hist_df.end[max_ind]) / 2
    print('Mode =', mode)
    
    return hist_df,mode
#end-proc
print('End   of defining procedure : get_mode :', datetime.datetime.now())