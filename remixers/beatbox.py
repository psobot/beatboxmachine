"""
Dependencies:
    Remixer
    lame (command line binary)
"""

from remixer import *
from echonest.selection import *
from echonest.sorting import *
from echonest.action import make_stereo
import math
import numpy

def avg(xArr):
    return round(float(sum(xArr)/len(xArr)),1)

def stddev(xArr):
    return "std"

def are_kicks(x):
    bright = x.timbre[1] < 20
    #flat =  x.timbre[2] < 0 
    attack = x.timbre[3] > 80
    return bright

def are_snares(x):
    loud = x.timbre[0] > 10
    bright = x.timbre[1] > 100 and x.timbre[1] < 150
    flat =  x.timbre[2] < 30
    attack = x.timbre[3] > 20
    return loud and bright and flat and attack

def are_hats(x):
    loud = x.timbre[0] < 45
    bright = x.timbre[1] > 80
    flat =  x.timbre[2] < 10
    attack = x.timbre[3] > 60
    what = x.timbre[4] < 40
    return loud and bright and flat and attack and what

class Beatbox(Remixer):
    template = {
      'hats': 'hat.wav',
      'kick': 'kick.wav',
      'snare': 'snare.wav'
        }

    def remix(self):
        """
            Remixing happens here. Take your input file from self.infile and write your remix to self.outfile.
            If necessary, self.tempfile can be used for temp files. 
        """
        self.log("Listening to beatbox track...", 30)
        self.original = audio.LocalAudioFile(self.infile)
        self.tag['tempo'] = self.original.analysis.tempo

        kicks = self.original.analysis.segments.that(are_kicks)
        snares = self.original.analysis.segments.that(are_snares)
        hats = self.original.analysis.segments.that(are_hats)

        # Time to replace
        self.log("Replacing beats...", 30)
        hat_sample = audio.AudioData(self.sample_path + self.template['hats'], sampleRate=44100, numChannels=2, verbose=False)
        kick_sample = audio.AudioData(self.sample_path + self.template['kick'], sampleRate=44100, numChannels=2, verbose=False)
        snare_sample = audio.AudioData(self.sample_path + self.template['snare'], sampleRate=44100, numChannels=2, verbose=False)

        if self.original.numChannels == 1:
            self.original = make_stereo(self.original)

        last = 0
        for segment in kicks:
            if last + len(kick_sample.data) > segment.start:
                truncated = kick_sample.data
                if self.original.sampleRate*segment.start + len(kick_sample.data) > len(self.original.data):
                    truncated = truncated[:len(self.original.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(kick_sample.data)])]
                self.original.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(truncated)] *= 0.4
                self.original.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(truncated)] += truncated
            last = segment.start

        last = 0
        for segment in hats:
            if last + len(hat_sample.data) > segment.start:
                truncated = hat_sample.data
                if self.original.sampleRate*segment.start + len(hat_sample.data) > len(self.original.data):
                    truncated = truncated[:len(self.original.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(hat_sample.data)])]
                self.original.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(truncated)] *= 0.4
                self.original.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(truncated)] += truncated
            last  = segment.start
        last = 0
        for segment in snares:
            if last + len(snare_sample.data) > segment.start:
                truncated = snare_sample.data
                if self.original.sampleRate*segment.start + len(snare_sample.data) > len(self.original.data):
                    truncated = truncated[:len(self.original.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(snare_sample.data)])]
                self.original.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(truncated)] *= 0.4
                self.original.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(truncated)] += truncated     
            last = segment.start

        self.log("Mastering...", 20)
        #audio.mix(empty, data, 0.5).encode(self.outfile)
        self.original.encode(self.outfile)
        self.updateTags(' (Beatbox Machine remix)')
        return self.outfile

if __name__ == "__main__":
    CMDRemix(Beatbox)

