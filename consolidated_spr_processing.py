#******************************************************************************************************************************************
# TITLE     : CONSOLIDATED_SPR_PROCESSING
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

#Screen-Printer PCB Detection

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

importlib.reload(routine_get_histogram)
importlib.reload(routine_get_pcb_dur)                 

#Set the folder name from which to read the csv file
FOLDER_NAME = 'csv_folders/helloworld-2019-05-23/'

#----------------------------------------------------
print('Reading the screen-printer csv file...')

#Get the data from screen-printer csv file
sprfile = pd.read_csv(FOLDER_NAME+'screenprinter.csv')
sprfile.columns = [c.replace('.', '_') for c in sprfile.columns]

print('Extracting proximity sensor data...')

#Proximity sensor data for Screen Printer
spr_pxend_file = sprfile.query('deviceid == "screenprinter_proximity_exit"').loc[:,['datatype','timestamp','deviceid','data_proximity']]
spr_pxend_file = spr_pxend_file.sort_values(by="timestamp")
spr_pxend_file = spr_pxend_file.reset_index()
spr_pxend_file = spr_pxend_file.iloc[:,1:len(spr_pxend_file.columns)]
spr_pxend_file['datetime'] = pd.to_datetime(spr_pxend_file.timestamp)

print('Extracting current meter data...')

#Extract details from current meter data
spr_curr_file = sprfile.query('deviceid == "screenprinter_plus_vaf"').loc[:,['datatype','timestamp','deviceid','data_A1','data_A2','data_A3']]
spr_curr_file = spr_curr_file.sort_values(by="timestamp")
spr_curr_file = spr_curr_file.reset_index()
spr_curr_file = spr_curr_file.iloc[:,1:len(spr_curr_file.columns)]
spr_curr_file = spr_curr_file.assign(tot_curr = spr_curr_file.data_A1)
spr_curr_file['datetime'] = pd.to_datetime(spr_curr_file.timestamp)

print('Size of spr_pxend_file =', spr_pxend_file.shape)
print('Size of spr_curr_file  =', spr_curr_file.shape)

print('Constructing the pcb level dataframe...')

#Construct PCB level dataframe using proximity sensor data
pcb_pxdata_spr = spr_pxend_file.query('data_proximity == 1.0').loc[:,['timestamp']]
pcb_pxdata_spr = pcb_pxdata_spr.reset_index()
pcb_pxdata_spr = pcb_pxdata_spr.iloc[:,1:len(pcb_pxdata_spr.columns)]
pcb_pxdata_spr = pcb_pxdata_spr.rename(columns={'timestamp':'dptr_tmstmp'})

#=============================================================================

print('--------------------------------------------------------------')
print('Collecting basic details and performing normalization...')
spr_timestamp = spr_curr_file.timestamp
spr_sig = spr_curr_file.tot_curr 
spr_nrm = (spr_sig - np.mean(spr_sig)) / np.std(spr_sig)   3Normalized signal

print('Performing quantization...')

#Uniform quantization with step-zise = 0.1
spr_acc = spr_nrm
spr_quant                                         \
= -0.50 * (spr_acc <  -0.50)                       \
- 0.40 * ((spr_acc >= -0.50) & (spr_acc < -0.40)) \
- 0.30 * ((spr_acc >= -0.40) & (spr_acc < -0.30)) \
- 0.20 * ((spr_acc >= -0.30) & (spr_acc < -0.20)) \
- 0.10 * ((spr_acc >= -0.20) & (spr_acc < -0.10)) \
+ 0.00 * ((spr_acc >= -0.10) & (spr_acc <  0.00)) \
+ 0.10 * ((spr_acc >=  0.00) & (spr_acc <  0.10)) \
+ 0.20 * ((spr_acc >=  0.10) & (spr_acc <  0.20)) \
+ 0.30 * ((spr_acc >=  0.20) & (spr_acc <  0.30)) \
+ 0.40 * ((spr_acc >=  0.30) & (spr_acc <  0.40)) \
+ 0.50 * ((spr_acc >=  0.40) & (spr_acc <  0.50)) \
+ 0.60 * ((spr_acc >=  0.50) & (spr_acc <  0.60)) \
+ 0.70 * ((spr_acc >=  0.60) & (spr_acc <  0.70)) \
+ 0.80 * ((spr_acc >=  0.70) & (spr_acc <  0.80)) \
+ 0.90 * ((spr_acc >=  0.80) & (spr_acc <  0.90)) \
+ 1.00 * ((spr_acc >=  0.90) & (spr_acc <  1.00)) \
+ 1.10 * ((spr_acc >=  1.00) & (spr_acc <  1.10)) \
+ 1.20 * ((spr_acc >=  1.10) & (spr_acc <  1.20)) \
+ 1.30 * ((spr_acc >=  1.20) & (spr_acc <  1.30)) \
+ 1.40 * ((spr_acc >=  1.30) & (spr_acc <  1.40)) \
+ 1.50 * ((spr_acc >=  1.40) & (spr_acc <  1.50)) \
+ 1.60 * ((spr_acc >=  1.50) & (spr_acc <  1.60)) \
+ 1.70 * ((spr_acc >=  1.60) & (spr_acc <  1.70)) \
+ 1.80 * ((spr_acc >=  1.70) & (spr_acc <  1.80)) \
+ 1.90 * ((spr_acc >=  1.80) & (spr_acc <  1.90)) \
+ 2.00 * (spr_acc >=  1.90)                       \
;

print('Conversion to ternary and binary...')
LOW=0.0; HIGH=2.0
spr_trnry = 2.0 * (spr_quant >= HIGH) + 1.0 * ((spr_quant >= LOW) & (spr_quant < HIGH)) + 0.0 * (spr_sig < LOW) 
spr_binry = 0.0 * (spr_quant >= HIGH) + 1.0 * ((spr_quant >= LOW) & (spr_quant < HIGH)) + 0.0 * (spr_sig < LOW) 

print('Constructing processed sataframe for SPR...')
filt_sig_spr = pd.DataFrame(columns=['timestamp','sig_curr','nrm_curr','quant_sig','trnry_sig','binry_sig'])
filt_sig_spr['timestamp'] = spr_timestamp
filt_sig_spr['sig_curr']  = spr_sig
filt_sig_spr['nrm_curr']  = spr_nrm
filt_sig_spr['quant_sig'] = spr_quant
filt_sig_spr['trnry_sig'] = spr_trnry
filt_sig_spr['binry_sig'] = spr_binry

print('Identifying the potential PCB detections...')
pcb_df = filt_sig_spr.query('binry_sig == 1.0').loc[:,['timestamp','quant_sig']]
pcb_df = pcb_df.reset_index()
pcb_df = pcb_df.rename(columns={'index':'orig_ind'})

print('Performing sensor fusion...')
#Sensor fusion between current-meter data and proximity data to identify PCB detections
spr_det_binry_sig = 0.0 * filt_sig_spr.binry_sig
for i in range(0,len(pcb_pxdata_spr)):
    
    curr_pxend_tmstmp = pcb_pxdata_spr.dptr_tmstmp[i]
    
    if (i == 0):
        temp_df = pcb_df.query('timestamp < @curr_pxend_tmstmp')
    else:
        temp_df = pcb_df.query('timestamp > @prev_pxend_tmstmp & timestamp < @curr_pxend_tmstmp')
    #end-if
    temp_df = temp_df.reset_index()
    temp_df = temp_df.iloc[:,1:len(temp_df.columns)]
    
    bin_count = len(temp_df)
    
    if (bin_count > 0):
        maxind = np.argmax(temp_df.quant_sig)
        origindmax = temp_df.orig_ind[maxind]
        spr_det_binry_sig[origindmax] = 1.0
    else:
        print('Bin-count is zero between:', prev_pxend_tmstmp, 'and', curr_pxend_tmstmp)
    #end-if 
    
    prev_pxend_tmstmp = curr_pxend_tmstmp
    
#end-for    
filt_sig_spr['det_binry_sig'] = spr_det_binry_sig

print('END   OF PROCESSING :', datetime.datetime.now())