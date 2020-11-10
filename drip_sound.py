
# generate pop texture
import numpy as np
import seaborn as sns
from scipy import signal
import math
import sys
import soundfile as sf

'''

This code will generate a dataset of textures consiting of drip. A 'drip' is a frequency sweep with decaying amplitude. 

The files are generated using 3 different parameters that are sampled over a range of values. The three parameters affect:
    rate (average events per second), 
    irregularity in temporal distribution (using a gaussian distribution around each evenly-spaced time value), and 
    the center frequency of bp filter

The parameter values are each sampled liniearly on an exponential scale:

rate = 2^r_exp  (so r_exp in [0,4] means the rate ranges from 2 to 16)
irregularity = .04*10^irreg_exp; sd = irregularity/events per second  (so irreg_exp in [0,1] means irregularity ranges from completely regular, to Poisson process)
cf = 440*2^cf_exp  (so cf_exp in [0,1] means cf ranges from 440 to 880, one octave)

For each parameter setting, first a "long" signal (of lentgth longDurationSecs) is generated, and then
it is sliced into segments (called variations) of a length desired for training. 

Example: If each parameter is sampled at 5 values, the long signal is 10 seconds and variationLength is 2 seconds,
then The the total amount of audio generated is 5*5*5*10= 1250 seconds of sound (about 25 hours; ~3Gb at 16K sr).
If each variation is 2 seconds, then there will be 10/2=5 variations for each parameter setting, and
5*5*5*5 = 625 files
'''

'''Frequency sweeper for a drip sound'''
def soundModel(centerFreq_Hz, bandwidth_Hz, fs, numSamples=1000):

    #drip specific parameters
    phase = 0
    start_Hz = centerFreq_Hz - bandwidth_Hz / 2
    stop_Hz = centerFreq_Hz + bandwidth_Hz / 2
    drip = [((stop_Hz - x)/(stop_Hz-start_Hz))*np.sin(phase + 2 * np.pi*x) for x in np.linspace(start_Hz, stop_Hz, numSamples, endpoint=False)]

    return drip

'''
   Take a list of event times, and return our signal of filtered pops at those times
'''
def elist2signal(elist, sigLenSecs, sr, cf, Q) :
    numSamples=sr*sigLenSecs
    sig=np.zeros(sigLenSecs*sr)
    for nf in elist :
        startsamp=int(round(nf*sr))%numSamples
        
        # create some deviation in center frequency
        cfsd = 1
        perturbedCf = cf*np.power(2,np.random.normal(scale=cfsd)/12)
        
        #print("perturbed CF is {}".format(perturbedCf))
        #   pop(ticksamps, len, krms, f0, Q, fs)
        sig=addin(soundModel(perturbedCf,Q, sr, 1000), sig,startsamp)
    return sig


def generateRandom(eventsPerSecond, sd, soundDurSecs, numSamples, sr=16000):
    return [(x+np.random.normal(scale=sd))%soundDurSecs for x in np.linspace(0, soundDurSecs, eventsPerSecond*soundDurSecs, endpoint=False)]

''' Generate events given a rate and irregularity'''
def generateEvents(eventsPerSecond, sd, soundDurSecs, numSamples, sr=16000):
    myevents=[(x+np.random.normal(scale=sd))%soundDurSecs for x in np.linspace(0, soundDurSecs, eventsPerSecond*soundDurSecs, endpoint=False)]
    sig=np.zeros(soundDurSecs*sr)
    for nf in myevents :
        #print("nf = {} and index is {}".format(nf, int(round(nf*sr))))
        sig[int(round(nf*sr))%numSamples]=1
    return sig

'''
    adds one (shorter) array in to another starting at startsamp in the second
'''
def addin(a,b,startsamp) :
    b[startsamp:startsamp+len(a)]=[sum(x) for x in zip(b[startsamp:startsamp+len(a)], a)]
    return b

''' 
Takes a parameter triplet and produces a sound
p1: rate, p2: irregularity, p3: cf
'''
def synthesize(parameters, sr, fname, outDir, numVariations, soundDurationSecs=4):

	r_exp = parameters[0]
	irreg_exp = parameters[1]
	cf_exp = parameters[2]

	# mapping to the right ranges
	eps=np.power(2,r_exp)
	irregularity=.1*irreg_exp*np.power(10,irreg_exp)
	sd=irregularity/eps
	cf=440*np.power(2,cf_exp)  #range over one octave from 440 to 880

	linspacesteps=int(eps*soundDurationSecs)
	linspacedur = linspacesteps/eps

	varDurationSecs=math.floor(soundDurationSecs/numVariations)
	variationSamples=sr*varDurationSecs

	# Rate and irregularity control the event generation. 
	eventtimes=[(x+np.random.normal(scale=sd))%soundDurationSecs for x in np.linspace(0, linspacedur, linspacesteps, endpoint=False)]

	print("Writing Wav files with Rate: ", eps, " Irregularity: ", sd, " and Central frequency: ", cf)

	for v in range(numVariations):
	        
		# Central frequency controls the Central frequency of bandpass filter
		sig = elist2signal(eventtimes, soundDurationSecs, sr, cf,  50)

        #print("Writing training files with Rate: ", eps, " Irregularity: ", sd, " and Central frequency: ", cf)

		# print(fname)
		sf.write(outDir + fname[v], sig[v*variationSamples:(v+1)*variationSamples], sr)

	#print("Check the files printed at ", outDir)


#Command-line Stub
#print(sys.argv[1])
#synthesizeSound(eval(sys.argv[1]), int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
