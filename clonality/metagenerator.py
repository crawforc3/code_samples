import os
args = os.listdir(r'.') 
samples_list=[]
for arg in args:
    #Make a list of samples
    if ".tsv" in arg and "metadata" not in arg:
        samples_list.append(arg)
    
metafile = open("meta.tsv", "w")
for samp in samples_list:
    metafile.write(samp + "\n")
    
metafile.close()
