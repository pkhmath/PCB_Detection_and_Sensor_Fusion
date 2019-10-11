#******************************************************************************************************************************************
# TITLE     : CONSOLIDATED_PP2_PROCESSING
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

#PP2 PCB Detection and Merging

#Import the libraries
import pandas as pd
import numpy as np
import scipy as sp

import csv
import datetime

import importlib

from matplotlib import pyplot as plt
from matplotlib import dates  as md 
from matplotlib.colors import LogNorm

print('START OF PROCESSING :', datetime.datetime.now())

#-------------------------------------------------
#Import routines
import routine_rawaccl_to_binryseq  
import routine_get_pcb_dur          
import routine_elim_spur_pcb        
import routine_get_pcb_level_data   
import routine_merging_algo         
import routine_merge_pxmty_algo 
import routine_rev_merge_pxmty_algo 

importlib.reload(routine_rawaccl_to_binryseq)  
importlib.reload(routine_get_pcb_dur)          
importlib.reload(routine_elim_spur_pcb)        
importlib.reload(routine_get_pcb_level_data)   
importlib.reload(routine_merging_algo)         
importlib.reload(routine_merge_pxmty_algo)
importlib.reload(routine_rev_merge_pxmty_algo)

FOLDER_NAME = 'csv_folders/helloworld-2019-05-03/'
print('FOLDER_NAME =', FOLDER_NAME)

#-----------------------------------------------------------
#Get the data from pp2 csv file
print('Reading PP2 csv file...')
pp2file = pd.read_csv(FOLDER_NAME+'pickandplace2.csv')
pp2file.columns = [c.replace('.', '_') for c in pp2file.columns]

#PP2 Proximity sensor data
print('Extracting proximity sensor data...')
pp2_pxend_file = pp2file.query('deviceid == "pickandplace2_proximity_exit"').loc[:,['datatype','timestamp','deviceid','data_proximity']]
pp2_pxend_file = pp2_pxend_file.sort_values(by="timestamp")
pp2_pxend_file = pp2_pxend_file.reset_index()
pp2_pxend_file = pp2_pxend_file.iloc[:,1:len(pp2_pxend_file.columns)]

#PP2 Vibration sensor data
print('Extracting vibration sensor data...')
pp2_vibr_file = pp2file.query('deviceid == "pickandplace2_vibration"').loc[:,['datatype','timestamp','deviceid','data_ax','data_ay','data_az']]
pp2_vibr_file = pp2_vibr_file.sort_values(by="timestamp")
pp2_vibr_file = pp2_vibr_file.reset_index()
pp2_vibr_file = pp2_vibr_file.iloc[:,1:len(pp2_vibr_file.columns)]
pp2_vibr_file = pp2_vibr_file.assign(net_accl = np.sqrt(pp2_vibr_file.data_ax**2 + pp2_vibr_file.data_ay**2 + pp2_vibr_file.data_az**2))

print('Size of pp2_pxend_file =', pp2_pxend_file.shape)
print('Size of pp2_vibr_file  =', pp2_vibr_file.shape)

#----------------------------------------------------------------------------------------------------------------
#Convert raw acceleration to binary sequence
LOWTHR  = 0.25
HIGHTHR = 0.80 
filt_sig_pp2 = routine_rawaccl_to_binryseq.rawaccl_to_binryseq(pp2_vibr_file,1,'Y','Y',LOWTHR,HIGHTHR)

#Detect PCBs and obtain PCB processing durations
pcb_data_pp2 = routine_get_pcb_dur.get_pcb_dur(filt_sig_pp2.binry_sig)

#Eliminate spuriois PCB detections
filt_sig_pp2['cor_binry_sig'] = routine_elim_spur_pcb.elim_spur_pcb(filt_sig_pp2.binry_sig,pcb_data_pp2,250)

#Recalculate PCB processing durations
pcb_data_pp2 = routine_get_pcb_dur.get_pcb_dur(filt_sig_pp2.cor_binry_sig)

#Obtain PCB level dataframe with weightages
pcb_level_pp2 = routine_get_pcb_level_data.get_pcb_level_data(filt_sig_pp2,pcb_data_pp2,50)

#-----------------------------------------------------------------------------------------------------------------
#Merging process (Two-step)
pcb_merge_pp2 = pcb_level_pp2
mrg_binry_pp2 = filt_sig_pp2.cor_binry_sig

THRESHOLD = 0.95
HIGH_END  = 1.50

iter_one = 0
iter_two = 0

PROC_ONE_END_FLAG = 0
while (PROC_ONE_END_FLAG == 0):
    
    iter_one = iter_one + 1
    print('PROC-ONE-ITERATION :', iter_one)
    
    pcb_merge_pp2,mrg_binry_pp2,no_of_merged_pcbs = routine_rev_merge_pxmty_algo.rev_merge_pxmty_algo    \
    (inp_df        = pcb_merge_pp2                                      \
    ,pxmty_df      = pp2_pxend_file      \
    ,inp_binry_sig = mrg_binry_pp2                         \
    ,THRESHOLD     = THRESHOLD                                               \
    ,HIGH_END      = HIGH_END                                                \
    )
    
    if (no_of_merged_pcbs == 0):
        PROC_ONE_END_FLAG = 1
    #end-if
    
    print ('=============================================')
    
#end-while

PROC_TWO_END_FLAG = 0
while(PROC_TWO_END_FLAG == 0):
    
    iter_two = iter_two + 1
    print('PROC-TWO-ITERATION :', iter_two)
    
    pcb_merge_pp2,mrg_binry_pp2,no_of_merged_pcbs = routine_merging_algo.merging_algo  \
    (inp_df        = pcb_merge_pp2                                   \
    ,inp_binry_sig = mrg_binry_pp2                                   \
    ,THRESHOLD     = THRESHOLD                                            \
    ,HIGH_END      = HIGH_END                                             \
    ) 
    
    if(no_of_merged_pcbs == 0):
        PROC_TWO_END_FLAG = 1
    #end-if
    
    print ('=============================================')
    
#end-while

filt_sig_pp2['mrg_binry_sig'] = mrg_binry_pp2

'''
#-----------------------------------------------------------------------------------------------------------
#Write processed info to csv file
print('Writing output files...')
filt_sig_pp2.to_csv(FOLDER_NAME+'PP2_Processed_DataFrame.csv')
pcb_merge_pp2.to_csv(FOLDER_NAME+'PP2_PCB_Merged_DataFrame.csv')
pp2_pxend_file.to_csv(FOLDER_NAME+'PP2_Proximity_Exit_DataFrame.csv')
#-----------------------------------------------------------------------------
'''

print('END OF PROCESSING :', datetime.datetime.now())