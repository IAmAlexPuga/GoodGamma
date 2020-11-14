import pyodbc

conn = pyodbc.connect('Driver={SQL Server};'
                      'Server=localhost;'
                      'Database=TestDB;'
                      'Trusted_Connection=yes;')
cursor = conn.cursor()

def main():
    #printFile("D:\\steam.sql")


def printFile(file):
    global COUNT
    fileLineCount = 0
    f = open(file, "r", encoding='utf8')
    fileByteCount = 0
    for line in f:
        cursor.execute(line)
        fileLineCount += 1
        if fileLineCount == 20:
            break
        if(fileLineCount % 10000 == 0):
            print("Current Line: " + str(fileLineCount))
    print(fileLineCount)
