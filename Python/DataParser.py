
MAXSIZE = 483183573 - 100000
tables = \
    ['Groups',
'Games_Genres',
'Games_Publishers',
'Games_Developers',
'Player_Summaries',
'Games_Daily',
'App_ID_Info',
'Games_1',
'Games_2']

COUNT = 0

newTable = ("-- Table structure for table ").lower()



def main():
    #printFile("D:\\steamData\\test.txt")
    #change to path of steam.sql file
    COUNT = 0

    printFile("E:\\steamData\\steam.sql")

def openNewFile(out):
    global COUNT
    out.close()
    return open('D:\\scriptOut\\test'+str(COUNT)+'.sql', 'w')

def initFile(out):
    fillData = open('D:\\fillData.txt', 'r')
    for line in fillData:
        out.write(line)

def isNewTable(line):
    llower = line.lower()
    cmpr = ""
    for table in tables:
        cmpr = table.lower()
        if newTable in llower and cmpr in llower:
            print("Table found: " + table)
            return True
    return False


def printFile(file):
    global COUNT
    fileLineCount = 0
    f = open(file, "r", encoding='utf8')
    out = open('D:\\scriptOut\\test'+str(COUNT)+'.sql', 'w')
    initFile(out)
    fileByteCount = 0
    for line in f:
        if len(line) + fileByteCount > MAXSIZE or isNewTable(line):
            COUNT += 1
            out = openNewFile(out)
            initFile(out)
            fileByteCount = 0
        #print(line)
        fileByteCount += len(line)
        out.write(line + '\n')
        fileLineCount += 1
        if(fileLineCount % 10000 == 0):
            print("Current Line: " + fileLineCount)
    print(fileLineCount)

main()