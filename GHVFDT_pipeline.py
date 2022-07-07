#File path location. 
pfd_path='/data/testpfd/pfds' # path of all pfd files for classification. It is required if scores=''
scores='' #Keep scores='' if scores not available
model='/data/non_ML_codes/pipeline/GHRSS_models/GHRSS1-3.model' #Necessary

#Use modules
fp_nulling=True
tp_nulling=True
schan=True

#packages
import os, subprocess, glob, psrchive
import numpy as np
import matplotlib.pyplot as plt
from nulling import pfd_data, nullsnr
from strongchan import snrcharm

current_path=os.getcwd()
if(scores==''):
	os.system('rm -r scores.arff')
	os.system('python2 CandidateScoreGenerators/ScoreGenerator.py -c '+pfd_path+' -o scores.arff --pfd --arff --dmprof')
	scores=current_path+'/scores.arff'

os.system('rm -r predict.txt*')
os.system('java -jar ML.jar -v -m'+model+' -o' +current_path+'/predict.txt -p' + scores+' -a1')

#Read GH-VFDT predict.txt and copy to pfd_select
with open('predict.txt','r') as f:
	lines=f.read()

#copy pfd files from pfd_path to pfd_select in pipeline folder
lines=lines.split('\n')[1:-1]
files=[i.split(',')[0] for i in lines]
os.system('rm -r pfd_select')
os.system('mkdir pfd_select')
for i in files:
	os.system('cp '+i+' pfd_select/')

#creating PDF files of ps files as ML_files.pdf
pfds=glob.glob('pfd_select/*.pfd')
os.system('rm -r *.pfd*')
for i in pfds:
	os.system('show_pfd -noxwin ' + i)

os.system('gs -dNOPAUSE -sDEVICE=pdfwrite -sOUTPUTFILE=ML_files.pdf -dBATCH *.ps')
os.system('rm -r *.pfd*')

#using filters
pfd_dat=[pfd_data(i) for i in pfds]
null_fp=[]
null_tp=[]
schan_rm=[]
for j in range(len(pfd_dat)):
	print(pfds[j])
	i=pfd_dat[j]
	fp=np.mean(i[:,0,:],axis=0)
	chans=fp.shape[0]
	fp=fp[int(chans*0.1):-int(chans*0.1)]
	tp=np.mean(i[:,0,:],axis=1)
	snrfp=nullsnr(fp)
	snrtp=nullsnr(tp)
	snrschan=snrcharm(fp)
	if(snrfp>4.0): #Threshold for fp nulling removed SNR
		null_fp.append(pfds[j])
	if(snrtp>4.0): #Threshold for tp nulling removed SNR
		null_tp.append(pfds[j])
	if(snrschan>4.0): #Threshold for Strong channel removed candidates SNR
		schan_rm.append(pfds[j])

# Using combination of filters
filtered=[]
if(schan==False):
	if(fp_nulling==True and tp_nulling==False):
		filtered=null_fp
	elif(fp_nulling==False and tp_nulling==True):
		filtered=null_tp
	elif(fp_nulling==True and tp_nulling==True):
		for i in null_fp:
			if i in null_tp:
				filtered.append(i)
else:
	if(fp_nulling==True and tp_nulling==False):
		for i in schan_rm:
			if i in null_fp:
				filtered.append(i)
	elif(fp_nulling==False and tp_nulling==True):
		for i in schan_rm:
			if i in null_tp:
				filtered.append(i)
	elif(fp_nulling==True and tp_nulling==True):
		for i in null_fp:
			if i in null_tp:
				if i in schan_rm:
					filtered.append(i)

#creating filtered files PDF
for i in filtered:
	os.system('show_pfd -noxwin ' + i)

os.system('gs -dNOPAUSE -sDEVICE=pdfwrite -sOUTPUTFILE=filtered.pdf -dBATCH *.ps')
os.system('rm -r filtered')
os.system('mkdir -p filtered')
os.system('cp *.ps filtered')
os.system('rm -r *.pfd*')
if(len(lines)<2):
	print("There were no positive candidates")

