# creates a e+ group file with all the idf models and epw files in folder.

import glob
import os

listIDF = glob.glob("*.idf")
listEPW = glob.glob("*.epw")

conteudo = ""
for i in listIDF:
	for epw in listEPW:
		conteudo = conteudo + os.getcwd()+"\\"+i+","+os.getcwd()+"\\"+epw+","+os.getcwd()+"\\"+epw[:-4]+"\\"+i[:-4]+",1\n"

posicao = os.getcwd().rfind("\\")+1
nome = os.getcwd()[posicao:]

with open(nome+"_group.epg", "w") as file:
	file.write(conteudo)