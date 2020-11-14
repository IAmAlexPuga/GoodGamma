
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

lastCount = 139165
COUNT = 0

newTable = ("-- Table structure for table ").lower()



def main():
    #printFile("D:\\steamData\\test.txt")
    #change to path of steam.sql file
    COUNT = 0

    printFile2("E:\\steamData\\steam.sql")

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
            print("Table found: " + table + " at count " + str(COUNT))
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
            print("Current Line: " + str(fileLineCount))
    print(fileLineCount)


def printFile2(file):
    global COUNT
    COUNT  = 223
    fileLineCount = 0
    f = open(file, "r", encoding='utf8')
    out = open('D:\\scriptOut\\test' + str(COUNT) + '.sql', 'w')
    initFile(out)
    fileByteCount = 0
    for line in f:

        if fileLineCount >= 139165:
            if len(line) + fileByteCount > MAXSIZE or isNewTable(line):
                COUNT += 1
                out = openNewFile(out)
                initFile(out)
                fileByteCount = 0
            # print(line)
            fileByteCount += len(line)

            line = parseData(line)
            out.write(line + '\n')
            fileLineCount += 1
            if (fileLineCount % 10000 == 0):
                print("Current Line: " + str(fileLineCount))
        fileLineCount += 1

    print(fileLineCount)


def parseData(line):
    #lines = line.split(' ',4)
    #source = lines[-1]
    #reGroup = lines[0] + " " + lines[1] + " " + lines[2] + " "  + lines[3]
    #sourceArr = source.split(',')
    #sarr = [lines[-1]]

    for item in line:
        if '\x8f' in item:
            item = 'd'

    #for item in sourceArr:
        #reGroup += +  " " + str(item)
    return line




main()