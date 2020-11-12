
# dependencies for file reading
import json
import sys
import itertools
import numpy as np
import os
import pop_sound
import drip_sound
import librosa # conda install -c conda-forge librosa

sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath("./src/paramTest"))))

from paramManager import paramManager
from Tf_record import tfrecordManager

print(paramManager)

paramArr = []
data = []

# inputs: file, folder?
with open(sys.argv[1]) as json_file:
	data = json.load(json_file)
	print("Reading parameters for generating ", data['soundname'], " texture.. ")
	for p in data['params']:
	
#	    print('Name: ' + p['pname'])
#	    print('Units: ' + p['units']) 
#	    print("Formula: " + p['formula'])
	    p['formula'] = eval("lambda *args: " + p['formula'])
#	    print('')
	    paramArr.append(p)

# print("Cartesian products of linear interpolation of parameters.....")

cartParam = []

# one way to generate parameters
for p in paramArr:
	cartParam.append(np.linspace(p["minval"], p["maxval"], p["nvals"], endpoint=True))

# read synth file
soundSynth = eval(data['soundname'])
sr = data['samplerate']

# if directory exists, then ok, or else create
filepath = os.path.dirname(os.path.realpath(data['soundname']))
outPath = os.path.join(filepath, data['soundname'])
if not os.path.isdir(outPath):
    os.mkdir(outPath)

print("Enumerating parameter combinations..")

'''
	for every combination of cartesian parameter
	for every variation 
		Create variation wav files
		Create variation parameter files
'''

enumParam = list(itertools.product(*cartParam))

#print("Combination of parameters")

for enumP in enumParam: # caretesian product of lists
	fname = '/' + data['soundname']

	'''Construct filenames with static parameters'''
	for paramNum in range(len(paramArr)):
		fname = fname + '--' + paramArr[paramNum]['pname'] + '-'+'{:05.2f}'.format(enumP[paramNum])

	vFilesWav = []
	vFilesParam = []	

	''' Construct variations filenames'''
	for v in range(data['numVariations']):
		vFilesWav.append(fname + '--v-'+'{:03}'.format(v)+'.wav') 
		vFilesParam.append(fname + '--v-'+'{:03}'.format(v)+'.params') 

	''' Synthesize wav files'''
	soundSynth.synthesize(enumP, sr, vFilesWav, outPath, data['numVariations'], data['soundDuration'])

	print("Writing parameter files")
	''' Create param files '''
	for v in range(data['numVariations']):
		pm=paramManager.paramManager(vFilesParam[v], outPath)
		pm.initParamFiles(overwrite=True)
		for pnum in range(len(paramArr)):
			pm.addParam(vFilesParam[v], paramArr[pnum]['pname'], [0,data['soundDuration']], [enumP[pnum], enumP[pnum]], units=paramArr[pnum]['units'], nvals=paramArr[pnum]['nvals'], minval=paramArr[pnum]['minval'], maxval=paramArr[pnum]['maxval'])

		#tfm=tfrecordManager.tfrecordManager(vFilesParam[v], outPath)
		#data,sr = librosa.core.load(outPath + fname + '--v-'+'{:03}'.format(v)+'.wav',sr=16000)
		#print(len(data))
		#tfm.addFeature(vFilesParam[v], 'audio', [0,len(data)], data, units='samples', nvals=len(data), minval=0, maxval=0)
		#for pnum in range(len(paramArr)):
		#	print(pnum)
		#	tfm.addFeature(vFilesParam[v], paramArr[pnum]['pname'], [0,data['soundDuration']], [enumP[pnum], enumP[pnum]], units=paramArr[pnum]['units'], nvals=paramArr[pnum]['nvals'], minval=paramArr[pnum]['minval'], maxval=paramArr[pnum]['maxval'])
		#tfm.writeRecordstoFile()