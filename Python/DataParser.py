


def main():
    #printFile("D:\\steamData\\test.txt")
    #change to path of steam.sql file
    printFile("D:\\steamData\\steam.sql")



def printFile(file):
    f = open(file, "r", encoding='utf8')
    out = open('D:\\steamData\\test.txt', 'w')
    for line in f:
        print(line)
        out.write(line + '\n')

main()