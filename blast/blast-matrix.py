#!/usr/bin/python

matrix_output = open('diffExpr.P1e-3_C2.matrix', 'r') #linux

blast_output = open("blastp.outfmt6", "r") #linux


class parse_blast(object):
    
    def __init__(self, line):
        #Strip end-of-line and split on tabs
        self.fields = line.strip("\n").split("\t")
        self.transcriptId, self.isoform = self.fields[0].split("|")
        self.swissStuff = self.fields[1].split("|")
        self.swissProtId = self.swissStuff[3]
        self.percentId = self.fields[2]

    #Function for filtering bsaed on percent ID
    def filterblast(self):
        return float(self.percentId) > 95
    
    #Returns the swissprotId 
    def __str__(self):
        return self.swissProtId

class parse_matrix(object):
    #Consider __init__ as a Constructor
    def __init__(self, matrix_lines):
        #Split and strip the matrix_lines into proper fields
        (self.protein, 
        self.Sp_ds, 
        self.Sp_hs, 
        self.Sp_log, 
        self.Sp_plat) = matrix_lines.strip("\n").split("\t")
        
        #Convert to SwissProtId if transcript is in the dictionary
        if self.protein in transSwiss:
            self.protein = transSwiss[self.protein]
            
    #Returns all the fields
    def __str__(self):
        return self.protein,
        self.Sp_ds,
        self.Sp_hs,
        self.Sp_log,
        self.Sp_plat

#List comprehension to print tuples and objects
def separate_tuples(one_tuple):
    return '\t'.join(str(x) for x in one_tuple)

#Create map for parsed blast objects
blastmap = map(parse_blast, blast_output.readlines())
#Filter the blast output based on percent ID
filtered = filter(parse_blast.filterblast, blastmap)
#Fill up a dictioanry to convert transcriptId to swissprot ID
transSwiss = {x.transcriptId:x for x in filtered}
#Create a map of matrix objects
matrixmap = map(parse_matrix, matrix_output.readlines()[1:])

#Print everything nice and neat
for matrixo in matrixmap:
    print(separate_tuples((matrixo.protein, 
                                        matrixo.Sp_ds, 
                                        matrixo.Sp_hs, 
                                        matrixo.Sp_log, 
                                        matrixo.Sp_plat)))
#Close everything up    
blast_output.close()
matrix_output.close()
