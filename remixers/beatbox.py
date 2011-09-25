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
    return round(min(xArr))

def stddev(xArr):
    return round(max(xArr))
'''
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
    bright = x.timbre[1] > 90
    flat =  x.timbre[2] < 0
    attack = x.timbre[3] > 70
    what = x.timbre[4] < 40
    return loud and bright and flat and attack and what
'''

def are_kicks(x):
    bright = x.timbre[1] < 30
    flat =  x.timbre[2] < -30
    return bright and flat

def are_snares(x):
    bright = x.timbre[1] > 35 and x.timbre[1] < 140
    flat =  x.timbre[2] < 9
    attack = x.timbre[3] > 5
    t9 = x.timbre[8] > -10
    return bright and flat and attack and t9

def are_hats(x):
    bright = x.timbre[1] > 30
    what = x.timbre[4] > 15
    return bright and what


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
        '''
        bad = []

        for i, segment in enumerate(self.original.analysis.segments):
            segment.encode("seg%s.mp3" % i)

        loudnesses = [x.timbre[0] for i, x in enumerate(self.original.analysis.segments) if i not in bad]
        brightnesses = [x.timbre[1] for i, x in enumerate(self.original.analysis.segments) if i not in bad]
        flatnesses = [x.timbre[2] for i, x in enumerate(self.original.analysis.segments) if i not in bad]
        attacks = [x.timbre[3] for i, x in enumerate(self.original.analysis.segments) if i not in bad]
        timbre5 = [x.timbre[4] for i, x in enumerate(self.original.analysis.segments) if i not in bad]
        timbre6 = [x.timbre[5] for i, x in enumerate(self.original.analysis.segments) if i not in bad]
        timbre7 = [x.timbre[6] for i, x in enumerate(self.original.analysis.segments) if i not in bad]
        timbre8 = [x.timbre[7] for i, x in enumerate(self.original.analysis.segments) if i not in bad]
        timbre9 = [x.timbre[8] for i, x in enumerate(self.original.analysis.segments) if i not in bad]
        timbre10 = [x.timbre[9] for i, x in enumerate(self.original.analysis.segments) if i not in bad]
        timbre11 = [x.timbre[10] for i, x in enumerate(self.original.analysis.segments) if i not in bad]
        timbre12 = [x.timbre[11] for i, x in enumerate(self.original.analysis.segments) if i not in bad]

        print "21: %s" % self.original.analysis.segments[21].timbre

        print "MINS"
        print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % ('loud','bright','flat','attack','t5','t6','t7','t8','t9','t10','t11','t12')
        print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (avg(loudnesses),avg(brightnesses),avg(flatnesses),avg(attacks),avg(timbre5),avg(timbre6),avg(timbre7),avg(timbre8),avg(timbre9),avg(timbre10),avg(timbre11),avg(timbre12))
        print
        print "MAXS"
        print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % ('loud','bright','flat','attack','t5','t6','t7','t8','t9','t10','t11','t12')
        print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (stddev(loudnesses),stddev(brightnesses),stddev(flatnesses),stddev(attacks),stddev(timbre5),stddev(timbre6),stddev(timbre7),stddev(timbre8),stddev(timbre9),stddev(timbre10),stddev(timbre11),stddev(timbre12))
        '''
        self.log("Sorting kicks and snares...", 10)
        kicks = self.original.analysis.segments.that(are_kicks)
        snares = self.original.analysis.segments.that(are_snares)
        hats = self.original.analysis.segments.that(are_hats)

        # Time to replace
        self.log("Replacing beats...", 20)
        hat_sample = audio.AudioData(self.sample_path + self.template['hats'], sampleRate=44100, numChannels=2, verbose=False)
        kick_sample = audio.AudioData(self.sample_path + self.template['kick'], sampleRate=44100, numChannels=2, verbose=False)
        snare_sample = audio.AudioData(self.sample_path + self.template['snare'], sampleRate=44100, numChannels=2, verbose=False)

        if self.original.numChannels == 1:
            self.original = make_stereo(self.original)

        empty = audio.AudioData(ndarray=numpy.zeros(((self.original.sampleRate * self.original.analysis.duration), 2), dtype=numpy.int16), numChannels=2, sampleRate=44100)

        last = 0
        for segment in kicks:
            if last + len(kick_sample.data) > segment.start:
                truncated = kick_sample.data
                if len(truncated) > len(empty.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(kick_sample.data)]):
                    truncated = truncated[:len(empty.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(kick_sample.data)])]
                empty.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(kick_sample.data)] += truncated
            last = segment.start

        last = 0
        for segment in snares:
            if last + len(snare_sample.data) > segment.start:
                truncated = snare_sample.data
                if len(truncated) > len(empty.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(snare_sample.data)]):
                    truncated = truncated[:len(empty.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(snare_sample.data)])]
                empty.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(snare_sample.data)] += truncated   
            last = segment.start
        for segment in hats:
            if last + len(hat_sample.data) > segment.start:
                truncated = hat_sample.data
                if len(truncated) > len(empty.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(hat_sample.data)]):
                    truncated = truncated[:len(empty.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(hat_sample.data)])]
                empty.data[self.original.sampleRate*segment.start:self.original.sampleRate*segment.start + len(hat_sample.data)] += truncated
            last  = segment.start

        self.log("Mastering...", 20)

        audio.mix(empty, self.original, 0.8).encode(self.outfile)
        self.updateTags(' (Beatbox Machine remix)')
        return self.outfile

if __name__ == "__main__":
    CMDRemix(Beatbox)

