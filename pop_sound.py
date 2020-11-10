
# generate pop texture
import numpy as np
import seaborn as sns
from scipy import signal
import math
import sys
import soundfile as sf

'''

This code will generate a dataset of textures consiting of pops. A 'pop' is a burst of noise filtered by a bandpass filter. 

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


'''
Generates a pop with a few random samples followed by a bandpass filter
@ticksamps - number os random samples to use (usually in the range [1,10] - 3 works well)
@len - total number of samples to generate (should be enough to include the ringing of the filter)
@krms - desired rms of the signal after filtering (not used currently)
@f0 - bandpass filter center frequency
@Q - bandpass filter Q value (<1 creates a long ringing tone at f0, >10 is shorter ringining wide-band noise)
fs - sample rate
'''
def soundModel(f0, Q, fs, len=1000) :

	# pop specific parameters
	ticksamps = 3
	krms = 0.6
	tick=2*np.random.rand(ticksamps)-1
	tick = np.pad(tick, (0, len-ticksamps), 'constant')
    
    # Design peak filter
	b, a = signal.iirpeak(f0, Q, fs)
	#use it
	tick=signal.lfilter(b, a, tick)

	if False :
		#print("original rms={}".format(math.sqrt(sum([x*x/ticksamps for x in tick]))))
		c=math.sqrt(ticksamps*krms*krms/sum([(x*x) for x in tick]))
		tick = [c*x for x in tick]
		#print("new rms={}".format(math.sqrt(sum([x*x/ticksamps for x in tick]))))
	else :
		maxfsignal=max(abs(tick))
		tick = tick*.9/maxfsignal

	return tick

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


#Command-line Stub
#print(sys.argv[1])
#synthesizeSound(eval(sys.argv[1]), int(sys.argv[2]), sys.argv[3], int(sys.argv[4]))
