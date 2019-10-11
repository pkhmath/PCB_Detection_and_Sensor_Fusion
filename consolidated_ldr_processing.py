#******************************************************************************************************************************************
# TITLE     : CONSOLIDATED_LDR_PROCESSING
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

#Line-Loader PCB Detection

#Import the libraries
import pandas as pd
import numpy  as np
import scipy  as sp

import csv
import datetime

import importlib

from matplotlib import pyplot as plt
from matplotlib import dates  as md 
from matplotlib.colors import LogNorm

print('START OF PROCESSING :', datetime.datetime.now())

#-------------------------------------------------
#Import routines
import routine_get_histogram
import routine_get_pcb_dur          
import routine_elim_ldng_pcb            

importlib.reload(routine_get_histogram)
importlib.reload(routine_get_pcb_dur)          
importlib.reload(routine_elim_ldng_pcb)        

#Set the folder name from which to access the csv file
FOLDER_NAME = 'csv_folders/helloworld-2019-05-23/'

#----------------------------------------------------
print('Reading the loader csv file...')

#Get the data from line-loader csv file
ldrfile = pd.read_csv(FOLDER_NAME+'loader.csv')
ldrfile.columns = [c.replace('.', '_') for c in ldrfile.columns]

print('Extracting the loader vibration data...')

#Extract essential LDR vibration data 
#For net-acceleration, only x and z components are considered
ldr_vibr_file = ldrfile.query('deviceid == "loader_vibration"').loc[:,['datatype','timestamp','deviceid','data_ax','data_ay','data_az','data_gx','data_gy','data_gz']]
ldr_vibr_file = ldr_vibr_file.sort_values(by="timestamp")
ldr_vibr_file = ldr_vibr_file.reset_index()
ldr_vibr_file = ldr_vibr_file.iloc[:,1:len(ldr_vibr_file.columns)]
ldr_vibr_file['datetime'] = pd.to_datetime(ldr_vibr_file.timestamp)
ldr_vibr_file = ldr_vibr_file.assign(net_accl = np.sqrt(ldr_vibr_file.data_ax**2 + ldr_vibr_file.data_az**2))

print('Size of ldr_vibr_file  =', ldr_vibr_file.shape)

#-------------------------------------------------------------------------
print('***Raw acceleration to binary conversion***')

#Raw-acceleration to binary sequence conversion
LDR_ROLLDEV_WIN = 75                                                 #Window size (in samples) for moving-deviation filtering
ldr_sig = ldr_vibr_file.net_accl                                     #Obtain net-acceleration
ldr_nrm = (ldr_sig - np.mean(ldr_sig)) / np.std(ldr_sig)             #Normalization
ldr_rlgdev = ldr_nrm.rolling(LDR_ROLLDEV_WIN,center=True).std()      #Perform moving-deviation filtering

#Discard the samples (NaN) lost due to rolling-deviation operation
LOSS = np.ceil(LDR_ROLLDEV_WIN / 2).astype(int)
ldr_cordev = np.array(ldr_rlgdev[0+LOSS:len(ldr_vibr_file)-LOSS])
ldr_cordev = pd.Series(ldr_cordev)

#Obtain timestamp series
ldr_timestamp = np.array(ldr_vibr_file.timestamp[0+LOSS:len(ldr_vibr_file)-LOSS])
ldr_timestamp = pd.Series(ldr_timestamp)

#Timestamp series in another format
ldr_datetime = np.array(pd.to_datetime(ldr_vibr_file.timestamp[0+LOSS:len(ldr_vibr_file)-LOSS]))
ldr_datetime = pd.Series(ldr_datetime)

print('Performing quantization...')

#Uniform quantization with step size = 0.5
ldr_quant \
= 0.0 * ((ldr_cordev >= 0.0) & (ldr_cordev < 0.5)) \
+ 0.5 * ((ldr_cordev >= 0.5) & (ldr_cordev < 1.0)) \
+ 1.0 * ((ldr_cordev >= 1.0) & (ldr_cordev < 1.5)) \
+ 1.5 * ((ldr_cordev >= 1.5) & (ldr_cordev < 2.0)) \
+ 2.0 * ((ldr_cordev >= 2.0) & (ldr_cordev < 2.5)) \
+ 2.5 * ((ldr_cordev >= 2.5) & (ldr_cordev < 3.0)) \
+ 3.0 * ((ldr_cordev >= 3.0) & (ldr_cordev < 3.5)) \
+ 3.5 * ((ldr_cordev >= 3.5) & (ldr_cordev < 4.0)) \
+ 4.0 * ((ldr_cordev >= 4.0) & (ldr_cordev < 4.5)) \
+ 4.5 * ((ldr_cordev >= 4.5) & (ldr_cordev < 5.0)) \
+ 5.0 * (ldr_cordev >= 5.0)                        \
;

print('Performing quantized to ternary conversion...')

#Conversion from quantozed signal to ternary signal
LOW_THRESH  = 0.0
HIGH_THRESH = 4.0
ldr_trnry                           \
= 1.0 * (ldr_quant >= HIGH_THRESH) \
+ 0.0 * (ldr_quant <= LOW_THRESH)  \
+ 0.5 * ((ldr_quant > LOW_THRESH) & (ldr_quant < HIGH_THRESH))

print('Performing ternary to binary conversion...')

#Conversion from ternary signal to binary signal
ldr_binry = ldr_trnry * 1.0
    
if (ldr_trnry[0] >= 0.5):
    ldr_binry[0] = 1.0
else:
    ldr_binry[0] = 0.0
#endif    
    
for i in range(1,len(ldr_trnry)):
    if (ldr_trnry[i] == 0.5):  
        ldr_binry[i] = ldr_binry[i-1]
    #endif
        
    if (i % 1000000 == 0):
        print('Processing at i = ',i)
    #end-if  
#end-for

print('Constructing the dataframe...')

#Construct the consolidated processed dataframe
filt_sig_ldr = pd.DataFrame(columns=['timestamp','datetime','rlng_accl','quant_sig','trnry_sig','binry_sig'])
filt_sig_ldr['timestamp'] = ldr_timestamp
filt_sig_ldr['datetime']  = ldr_datetime
filt_sig_ldr['rlng_accl'] = ldr_cordev
filt_sig_ldr['quant_sig'] = ldr_quant
filt_sig_ldr['trnry_sig'] = ldr_trnry
filt_sig_ldr['binry_sig'] = ldr_binry

#Detect PCBs and obtain PCB processing durations
pcb_data_ldr = routine_get_pcb_dur.get_pcb_dur(filt_sig_ldr.binry_sig)

#Eliminate PCB loading events
filt_sig_ldr['cor_binry_sig'] = routine_elim_ldng_pcb.elim_ldng_pcb(ldr_binry,pcb_data_ldr,1000)

#Recalculate PCB processing durations
pcb_data_ldr = routine_get_pcb_dur.get_pcb_dur(filt_sig_ldr.cor_binry_sig)

#Obtain local modes for PCB active duration, and also display vital statistics about machine
THRESHOLD = 200000
HISTBIN_WINDOW = 50
ldr_mode_df = routine_get_histogram.get_mode_df(pcb_data_ldr,THRESHOLD,HISTBIN_WINDOW)

print('Mode calculated at :', datetime.datetime.now())
    
if (len(pcb_data_ldr) > 0):
    avg_actv_dur = np.mean(pcb_data_ldr.pcb_actv_dur)
    med_actv_dur = np.median(pcb_data_ldr.pcb_actv_dur)
    dev_actv_dur = np.std(pcb_data_ldr.pcb_actv_dur)
    util_factor  = np.sum(pcb_data_ldr.pcb_actv_dur) / len(filt_sig_ldr) 
    
    print('Number of boards detected        =', len(pcb_data_ldr))
    print('Machine utilization factor       =', util_factor*100, '%')
    print('Average   board active duration  =', avg_actv_dur / 75, 'secs')
    print('Median    board active duration  =', med_actv_dur / 75, 'secs')
    print('Deviation board active duration  =', dev_actv_dur / 75, 'secs')
else:
    print('No PCB identified')
#end-if
    
#Obtain PCB level dataframe
pcb_level_ldr = pd.DataFrame(columns=['arvl_index','arvl_tmstmp','dptr_index','dptr_tmstmp','proc_dur','weightage'])

for i in range(0,len(pcb_data_ldr)):
    arvl_index   = pcb_data_ldr.arvl_index[i]
    arvl_tmstmp  = filt_sig_ldr.timestamp[arvl_index]
    dptr_index   = pcb_data_ldr.dptr_index[i]
    dptr_tmstmp  = filt_sig_ldr.timestamp[dptr_index]
    proc_dur = pd.Timedelta(pd.Timestamp(dptr_tmstmp) - pd.Timestamp(arvl_tmstmp)).total_seconds()
    
    mod_actv_dur = np.asscalar(ldr_mode_df.query('(str_index <= @arvl_index) & (end_index >= @dptr_index)').loc[:,'local_mode'])
    weightage    = pcb_data_ldr.pcb_actv_dur[i] / mod_actv_dur
        
    data = pd.DataFrame([[arvl_index,arvl_tmstmp,dptr_index,dptr_tmstmp,proc_dur,weightage]],columns=pcb_level_ldr.columns)
    pcb_level_ldr = pcb_level_ldr.append(data)
    del data
#end-for

pcb_level_ldr = pcb_level_ldr.reset_index()
pcb_level_ldr = pcb_level_ldr.iloc[:,1:len(pcb_level_ldr.columns)]

#-----------------------------------------------------------------------------------------------------------
'''
#Write processed info to csv file
print('Writing to files...')
filt_sig_ldr.to_csv(FOLDER_NAME+'LDR_Processed_DataFrame.csv')
pcb_level_ldr.to_csv(FOLDER_NAME+'LDR_PCB_Level_DataFrame.csv')

#-----------------------------------------------------------------------------
'''

print('END OF PROCESSING :', datetime.datetime.now())

#-----------------------------------------------------



