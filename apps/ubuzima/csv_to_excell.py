#!/usr/local/bin/python
# Tool to convert CSV files (with configurable delimiter and text wrap
# character) to Excel spreadsheets.
import string
import sys
import getopt
import re
import os
import os.path
import csv
from pyExcelerator import *

def usage():
  """ Display the usage """
  print "Usage:" + sys.argv[0] + " [OPTIONS] csvfile"
  print "OPTIONS:"
  print "--title|-t: If set, the first line is the title line"
  print "--lines|-l n: Split output into files of n lines or less each"
  print "--sep|-s c [def:,] : The character to use for field delimiter"
  print "--output|o : output file name/pattern"
  print "--help|h : print this information"
  sys.exit(2)

def openExcelSheet(outputFileName):
  """ Opens a reference to an Excel WorkBook and Worksheet objects """
  workbook = Workbook()
  worksheet = workbook.add_sheet("Sheet 1")
  return workbook, worksheet

def writeExcelHeader(worksheet, titleCols):
  """ Write the header line into the worksheet """
  cno = 0
  for titleCol in titleCols:
    worksheet.write(0, cno, titleCol)
    cno = cno + 1

def writeExcelRow(worksheet, lno, columns):
  """ Write a non-header row into the worksheet """
  cno = 0
  for column in columns:
    worksheet.write(lno, cno, column)
    cno = cno + 1

def closeExcelSheet(workbook, outputFileName):
  """ Saves the in-memory WorkBook object into the specified file """
  workbook.save(outputFileName)

def getDefaultOutputFileName(inputFileName):
  """ Returns the name of the default output file based on the value
      of the input file. The default output file is always created in
      the current working directory. This can be overriden using the
      -o or --output option to explicitly specify an output file """
  baseName = os.path.basename(inputFileName)
  rootName = os.path.splitext(baseName)[0]
  return string.join([rootName, "xls"], '.')

def renameOutputFile(outputFileName, fno):
  """ Renames the output file name by appending the current file number
      to it """
  dirName, baseName = os.path.split(outputFileName)
  rootName, extName = os.path.splitext(baseName)
  backupFileBaseName = string.join([string.join([rootName, str(fno)], '-'), extName], '')
  backupFileName = os.path.join(dirName, backupFileBaseName)
  try:
    os.rename(outputFileName, backupFileName)
  except OSError:
    print "Error renaming output file:", outputFileName, "to", backupFileName, "...aborting"
    sys.exit(-1)

def validateOpts(opts):
  """ Returns option values specified, or the default if none """
  titlePresent = False
  linesPerFile = -1
  outputFileName = ""
  sepChar = ","
  for option, argval in opts:
    if (option in ("-t", "--title")):
      titlePresent = True
    if (option in ("-l", "--lines")):
      linesPerFile = int(argval)
    if (option in ("-s", "--sep")):
      sepChar = argval
    if (option in ("-o", "--output")):
      outputFileName = argval
    if (option in ("-h", "--help")):
      usage()
  return titlePresent, linesPerFile, sepChar, outputFileName

def main():
  """ This is how we are called """
  try:
    opts,args = getopt.getopt(sys.argv[1:], "tl:s:o:h", ["title", "lines=", "sep=", "output=", "help"])
  except getopt.GetoptError:
    usage()
  if (len(args) != 1):
    usage()
  inputFileName = args[0]
  try:
    inputFile = open(inputFileName, 'r')
  except IOError:
    print "File not found:", inputFileName, "...aborting"
    sys.exit(-1)
  titlePresent, linesPerFile, sepChar, outputFileName = validateOpts(opts)
  if (outputFileName == ""):
    outputFileName = getDefaultOutputFileName(inputFileName)
  workbook, worksheet = openExcelSheet(outputFileName)
  fno = 0
  lno = 0
  titleCols = []
  reader = csv.reader(inputFile, delimiter=sepChar)
  for line in reader:
    if (lno == 0 and titlePresent):
      if (len(titleCols) == 0):
        titleCols = line
      writeExcelHeader(worksheet, titleCols)
    else:
      writeExcelRow(worksheet, lno, line)
    lno = lno + 1
    if (linesPerFile != -1 and lno >= linesPerFile):
      closeExcelSheet(workbook, outputFileName)
      renameOutputFile(outputFileName, fno)
      fno = fno + 1
      lno = 0
      workbook, worksheet = openExcelSheet(outputFileName)
  inputFile.close()
  closeExcelSheet(workbook, outputFileName)
  if (fno > 0):
    renameOutputFile(outputFileName, fno)

if __name__ == "__main__":
  main()
