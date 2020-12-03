import sys
import psycopg2

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget,QTableWidgetItem,QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5.QtGui import QIcon, QPixmap

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import mysql.connector
import matplotlib.pyplot as plt

import numpy as np
from textwrap import wrap


qtCreatorFile = "Steam_Data_App.ui" # Enter file here.
# credentials 
# update 
sql_user = 'root'
sql_pass = 'password'
sql_host = '127.0.0.1'
sql_db = 'steam_data'
sql_port = 3306


Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

# class for matplotlib graphs
class Canvas(FigureCanvas):
    def __init__(self, parent):
        self.fig, self.ax = plt.subplots(figsize=(5.15,3.9), dpi=100)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ylabel = ""
        self.xlabel = ""
        self.title = ""
        self.suptitle = ""
        self.heightSpacing = .01
        self.price = None
        self.x = []
        self.y = []
        self.move(633,395)
        self.avg = 0
        self.show()        
        
    # plot bar chart    
    def plot_chart(self):
        x = np.array(self.x)
        y = np.array(self.y)
        rects = self.ax.bar(x,y)
        plt.bar(x,y)
        plt.ylabel(self.ylabel)
        plt.xlabel(self.xlabel)
        plt.title(self.title)
        plt.suptitle(self.suptitle)
    
        # shows the value of the bar
        for rect in rects:
            height = rect.get_height() - 4
            text_height = rect.get_height()
            self.ax.text(rect.get_x() + rect.get_width() / 2., self.heightSpacing * height,'%d' % int(text_height),ha='center', va='bottom', color=((0,0,0)), size=6)
            if not (self.price is None):
                self.ax.text(rect.get_x() + rect.get_width() / 2., 1, '%d' % int(height), ha='center',
                        va='bottom')
    
    
        if x.size > 1:
            namesSpaced = ['\n'.join(wrap(i, 12)) for i in x]
            plt.xticks(x, namesSpaced, rotation=90)
            self.fig.tight_layout()
            
        self.ax.tick_params(axis='x', which='major', labelsize=7)
        self.fig.patch.set_facecolor('beige')
        self.ax.set_facecolor('ivory')
     
    # plot scatterplot
    def scatterPlot(self):
        x = np.array(self.x)
        y = np.array(self.y)
        plt.scatter(x, y)
        plt.ylabel(self.ylabel)
        plt.xlabel(self.xlabel)
        plt.title(self.title)
        plt.suptitle(self.suptitle)
        
        self.avg = "{:.2f}".format(self.avg)

        plt.gcf().text(0.68, 0.73, "avg = " + str(self.avg) + "\nmin = " + str(x[1])+ "\nmax = " + str(x[-1]) , fontsize=12)
        self.fig.patch.set_facecolor('beige')
        self.ax.set_facecolor('silver')
      
# main window class
class steam_App(QMainWindow):
    def __init__(self):
        super(steam_App, self).__init__()
        self.ui = Ui_MainWindow()
        self.LIMIT = 11
        self.ui.setupUi(self)
        self.loadOptionList()
        self.ui.optionList.currentTextChanged.connect(self.optionChanged)
        self.ui.game_table.itemSelectionChanged.connect(self.gameStat)
        self.ui.searchButton_2.clicked.connect(self.getGamesHelper)
        self.ui.removeButton.clicked.connect(self.clearFilter)
        self.ui.searchButton.clicked.connect(self.searchGames)

    # function to execute sql query
    def executeQuery(self, sql_str):
        try: 
            conn = mysql.connector.connect(user=sql_user, password=sql_pass,
                                           host=sql_host,database=sql_db, port=sql_port)
        except:
            print('Unable to connect to the database!')
        cur=conn.cursor(buffered=True)
        cur.execute(sql_str)
        conn.commit()
        results = cur.fetchall()
        conn.close()
        return results
        
    # load initial options
    def loadOptionList(self):
        self.ui.optionList.clear()
        #sql_str = "SELECT distinct b_state FROM Business ORDER BY b_state;"
        try:
            results = ("All Games",
                       "Best Ratings",
                       "Most Purchased",
                       "Game Recommendation: User",
                       "Game Recommendation: Business",
                       "Price Points")
            for item in results:
                self.ui.optionList.addItem(item)
        except:
            #print("Query 1 failed!")
            pass
        
        self.ui.optionList.setCurrentIndex(-1)
        self.ui.optionList.clearEditText()

    # function for when option is selected
    def optionChanged(self):
        self.ui.outputTable.clear()
        self.ui.typeList.clear()
        self.ui.genreList.clear()
        op = self.ui.optionList.currentText()
        if (self.ui.optionList.currentIndex()>=0):
            # show option lists for statistics search
            if op == "All Games" or op == "Best Ratings" or op == "Price Points" or op == "Most Purchased":
                try:
                    results = self.executeQuery("select distinct Genre from games_genres;")
                    for row in results:
                        self.ui.genreList.addItem(row[0])
                    results2 = self.executeQuery("select distinct Type from app_id_info;")
                    for row in results2:
                        self.ui.typeList.addItem(row[0])
                    results3 = ("Free to Play",
                                "Under $5.00",
                                "$5.00 - $10.00",
                                "$10.00 - $20.00",
                                "$20.00 - $50.00",
                                "$50.00 - $60.00",
                                "$60.00 - $100.00",
                                "Over $100.00")
                    for item in results3:
                        self.ui.priceList.addItem(item)
                    self.ui.priceList.setCurrentIndex(-1)
                    
                except:
                    print("Query failed!")

            else:
                pass
        else:
            pass
    
    # helper class for games
    def getGamesHelper(self):
        # store user option selections
        if (len(self.ui.genreList.selectedItems()) > 0):
            gen = self.ui.genreList.selectedItems()[0].text()
            genre_str = "and g.Genre = '" + gen + "' "
        elif (len(self.ui.genreList.selectedItems()) == 0):
            genre_str = ""
        if (len(self.ui.typeList.selectedItems()) > 0):
            type_sel = self.ui.typeList.selectedItems()[0].text()
            type_str = "and a.Type = '" + type_sel + "' "
        elif (len(self.ui.typeList.selectedItems()) == 0):
            type_str = ""
        
        if (self.ui.priceList.currentIndex() > -1):
            price = self.ui.priceList.currentText()
            if price == "Free to Play":
                priceP = 0
                price_str = "and a.Price = '" + str(priceP) + "' "
            elif price == "Under $5.00":
                priceP = 0
                priceT = 5
                price_str = "and a.Price > '" + str(priceP) + "' and a.Price < '" + str(priceT) + "' "
            elif price == "$5.00 - $10.00":
                priceP = 5
                priceT = 10
                price_str = "and a.Price > '" + str(priceP) + "' and a.Price < '" + str(priceT) + "' "
            elif price == "$10.00 - $20.00":
                priceP = 10
                priceT = 20
                price_str = "and a.Price > '" + str(priceP) + "' and a.Price < '" + str(priceT) + "' "
            elif price == "$20.00 - $50.00":
                priceP = 20
                priceT = 50
                price_str = "and a.Price > '" + str(priceP) + "' and a.Price < '" + str(priceT) + "' "
            elif price == "$50.00 - $60.00":
                priceP = 50
                priceT = 60
                price_str = "and a.Price > '" + str(priceP) + "' and a.Price < '" + str(priceT) + "' "
            elif price == "$60.00 - $100.00":
                priceP = 60
                priceT = 100
                price_str = "and a.Price > '" + str(priceP) + "' and a.Price < '" + str(priceT) + "' "
            elif price == "Over $100.00":
                priceP = 100
                price_str = "and a.Price > '" + str(priceP) + "' "
            
        elif (self.ui.priceList.currentIndex() == -1):
            price_str = ""
        
        self.getGames(genre_str, type_str, price_str)
        
    # function to get games from sql server based on options selected
    def getGames(self, gen, type_sel, price):
        self.ui.outputTable.clear()
        try: 
            criteria = self.ui.optionList.currentText()
            if criteria == "All Games":
                temp_str = "select distinct a.Title, a.Rating, a.Price, a.Type, g.Genre " + \
                            "from app_id_info a, games_genres g " + \
                            "where a.appid = g.appid " + \
                            gen + \
                            type_sel + \
                            price + \
                            "group by a.Title " + \
                            "order by a.Title;"
                
                results = self.executeQuery(temp_str)
                self.insertGames(results)
            
            elif criteria == "Best Ratings":
                temp_str = "select distinct a.Title, a.Rating, a.Price, a.Type, g.Genre " + \
                            "from app_id_info a, games_genres g " + \
                            "where a.appid = g.appid and " + \
                            "a.Rating > 70 " + \
                            gen + \
                            type_sel + \
                            price + \
                            "group by a.Title " + \
                            "order by a.Rating desc;"
                            
                graph_str = "select distinct a.Title, a.Rating, a.Price, a.Type, g.Genre " + \
                            "from app_id_info a, games_genres g " + \
                            "where a.appid = g.appid and " + \
                            "a.Rating > 70 " + \
                            gen + \
                            type_sel + \
                            price + \
                            "group by a.Title " + \
                            "order by a.Rating desc " + \
                            "limit " + str(self.LIMIT) + ";"
                
                results = self.executeQuery(temp_str)
                graph_results = self.executeQuery(graph_str)
                self.insertGames(results)
                self.bestRating(graph_results)
                
            
            
            # for most purchased, a temp table was created for speed
            #
            # CREATE TABLE temp_purchased 
            # select app_id_info.title, app_id_info.appid, app_id_info.Type, app_id_info.Price, app_id_info.Rating, count(app_id_info.appid) as purchases 
            # from app_id_info natural join games_2
            # where app_id_info.appid = games_2.appid
            # group by app_id_info.appid 
            # order by purchases desc;
            elif criteria == "Most Purchased":
                temp_str = "select a.title, a.purchases, a.Rating, a.Price, a.Type, g.Genre " + \
                            "from temp_purchased a, games_genres g " + \
                            "where a.appid = g.appid " + \
                            gen + \
                            type_sel + \
                            price + \
                            "group by a.appid " + \
                            "order by purchases desc;"
                
                graph_str = "select a.title, a.purchases, a.Rating, a.Price, a.Type, g.Genre " + \
                            "from temp_purchased a, games_genres g " + \
                            "where a.appid = g.appid " + \
                            gen + \
                            type_sel + \
                            price + \
                            "group by a.appid " + \
                            "order by purchases desc " + \
                            "limit " + str(self.LIMIT) + ";"
                
                results = self.executeQuery(temp_str)
                graph_results = self.executeQuery(graph_str)
                self.insertGamesPurchased(results)
                self.mostPurchased(graph_results)
                
            elif criteria == "Price Points":
                temp_str = 'select a.Price , count(a.Price) as numGamesPriced ' + \
                            'from app_id_info a, games_genres g ' + \
                            'where a.appid = g.appid and ' + \
                            'a.Price < 100 ' + \
                            gen + \
                            type_sel + \
                            price + \
                            'group by a.Price order by a.Price asc;'
                
                graph_str = 'select a.Price , count(a.Price) as numGamesPriced ' + \
                            'from app_id_info a, games_genres g ' + \
                            'where a.appid = g.appid and ' + \
                            'a.Price < 100 ' + \
                            gen + \
                            type_sel + \
                            price + \
                            'group by a.Price order by a.Price asc;'

                results = self.executeQuery(temp_str)
                self.insertGamesPrice(results, graph_str)

        except:
            pass
    
    # insert all games into table
    def insertGames(self, results):
        try:
            if (len(results) > 0):
                style = "::section {""background-color: #f3f3f3; }"
                self.ui.outputTable.horizontalHeader().setStyleSheet(style)
                self.ui.outputTable.setColumnCount(len(results[0]))
                self.ui.outputTable.setRowCount(len(results))
                self.ui.outputTable.setHorizontalHeaderLabels(['Title', 'Rating', 'Price', 'Type', 'Genre'])
                currentRowCount = 0
                for row in results:
                    for colCount in range (0,len(results[0])):
                        self.ui.outputTable.setItem(currentRowCount,colCount,QTableWidgetItem(str(row[colCount])))
                    currentRowCount += 1
                #self.ui.outputTable.resizeColumnsToContents()
                
            else:
                self.ui.outputTable.setColumnCount(5)
                self.ui.outputTable.setHorizontalHeaderLabels(['Title', 'Rating', 'Price', 'Type', 'Genre'])
            
            self.ui.outputTable.setColumnWidth(0, 200)
            self.ui.outputTable.setColumnWidth(1, 50)
            self.ui.outputTable.setColumnWidth(2, 60)
            self.ui.outputTable.setColumnWidth(3, 60)
            self.ui.outputTable.setColumnWidth(4, 60)
        
        except:
            print("Query 4 failed!")
        
    # insert games purchased into table
    def insertGamesPurchased(self, results):
        try:
            if (len(results) > 0):
                style = "::section {""background-color: #f3f3f3; }"
                self.ui.outputTable.horizontalHeader().setStyleSheet(style)
                self.ui.outputTable.setColumnCount(len(results[0]))
                self.ui.outputTable.setRowCount(len(results))
                self.ui.outputTable.setHorizontalHeaderLabels(['Title', 'Purchases', 'Rating', 'Price', 'Type', 'Genre'])
                currentRowCount = 0
                for row in results:
                    for colCount in range (0,len(results[0])):
                        self.ui.outputTable.setItem(currentRowCount,colCount,QTableWidgetItem(str(row[colCount])))
                    currentRowCount += 1
                #self.ui.outputTable.resizeColumnsToContents()
                
            else:
                self.ui.outputTable.setColumnCount(6)
                self.ui.outputTable.setHorizontalHeaderLabels(['Title', 'Purchases', 'Rating', 'Price', 'Type', 'Genre'])
            
            self.ui.outputTable.setColumnWidth(0, 200)
            self.ui.outputTable.setColumnWidth(1, 80)
            self.ui.outputTable.setColumnWidth(2, 50)
            self.ui.outputTable.setColumnWidth(3, 50)
            self.ui.outputTable.setColumnWidth(4, 50)
            self.ui.outputTable.setColumnWidth(5, 50)
        
        except:
            print("Query 5 failed!")
    
    # insert price points into table
    def insertGamesPrice(self, results, graph_str):
        try:
            if (len(results) > 0):
                style = "::section {""background-color: #f3f3f3; }"
                self.ui.outputTable.horizontalHeader().setStyleSheet(style)
                self.ui.outputTable.setColumnCount(len(results[0]))
                self.ui.outputTable.setRowCount(len(results))
                self.ui.outputTable.setHorizontalHeaderLabels(['Price', 'Number of Games'])
                currentRowCount = 0
                for row in results:
                    for colCount in range (0,len(results[0])):
                        self.ui.outputTable.setItem(currentRowCount,colCount,QTableWidgetItem(str(row[colCount])))
                    currentRowCount += 1
                #self.ui.outputTable.resizeColumnsToContents()
                
            else:
                self.ui.outputTable.setColumnCount(2)
                self.ui.outputTable.setHorizontalHeaderLabels(['Price', 'Number of Games'])
            
            self.ui.outputTable.setColumnWidth(0, 80)
            self.ui.outputTable.setColumnWidth(1, 80)
            
            graph_results = self.executeQuery(graph_str)
            self.pricePoints(graph_results)
            
        except:
            print("Query 6 failed!")
            
    # function for clear filter button
    def clearFilter(self):
        self.ui.genreList.clearSelection()
        self.ui.typeList.clearSelection()
        self.ui.priceList.setCurrentIndex(-1)
           
    # set up ratings graph
    def bestRating(self, results):
        names = []
        ratings = []

        for (name, rating, price, type, genre) in results:
            names.append(name)
            ratings.append(rating)
        
        # set up bar chart
        chart = Canvas(self)
        chart.title = "Best Rated Games"
        chart.xlabel = "Game Name"
        chart.ylabel = "Rating"
        chart.subtitle = "2016"
        chart.x = names
        chart.y = ratings
        chart.plot_chart()
        
    # set up most purhcased graph
    def mostPurchased(self, results):
        names = []
        purchases = []
    
        for (name, purchase, rating, price, type, genre) in results:
            names.append(name)
            purchases.append(purchase)
        
        # set up bar chart
        chart = Canvas(self)
        chart.title = "Most Purchased Games"
        chart.xlabel = "Game Name"
        chart.ylabel = "Purchases"
        chart.subtitle = "2016"
        chart.x = names
        chart.y = purchases
        chart.plot_chart()
        #self.ui.mplWindow.setItem(chart)    
    
    # set up price points scatterplot
    def pricePoints(self, results):
        prices = []
        counts = []
        
        priceTotal = 0
        numItems = 0
        for (price, count) in results:
          prices.append(price)
          counts.append(count)
          if price > 0:
            numItems += 1
            priceTotal += price
        
        # set up scatterplot
        chart = Canvas(self)
        chart.title = "Game Price Points"
        chart.xlabel = "Prices"
        chart.ylabel = "Number of Games"
        chart.subtitle = "2016"
        chart.x = prices
        chart.y = counts
        chart.avg = priceTotal/numItems
        chart.scatterPlot()
    
    # game title search bar
    def searchGames(self):
        if (len(self.ui.searchBar.text()) > 0):
            game = self.ui.searchBar.text()
            
            search_str = "select distinct a.Title, a.Rating, a.Price, a.Type, g.Genre " + \
                            "from app_id_info a, games_genres g " + \
                            "where a.appid = g.appid " + \
                            "and a.Title LIKE '%" + game + "%' " + \
                            "group by a.Title " + \
                            "order by a.Title;"
            results = self.executeQuery(search_str)
            self.gameTitleTable(results)
        else:
            self.ui.searchBar.setPlaceholderText("Enter Game Title")
    
    # add games to table after searching
    def gameTitleTable(self, results):
        names = []
        for (name, rating, price, type, genre) in results:
            names.append(name)
            
        try:
            if (len(names) > 0):
                style = "::section {""background-color: #f3f3f3; }"
                self.ui.game_table.horizontalHeader().setStyleSheet(style)
                self.ui.game_table.setColumnCount(1)
                self.ui.game_table.setRowCount(len(names))
                self.ui.game_table.setHorizontalHeaderLabels(['Title'])
                currentRowCount = 0
                for item in names:
                    self.ui.game_table.setItem(currentRowCount,0,QTableWidgetItem(item))
                    currentRowCount += 1
                    
                #self.ui.outputTable.resizeColumnsToContents()
                
            else:
                self.ui.game_table.setColumnCount(1)
                self.ui.game_table.setHorizontalHeaderLabels(['Title'])
            
            #self.ui.outputTable.setColumnWidth(0, 200)
        except:
            print("failed")
          
    # game statitstic information
    def gameStat(self):
        self.ui.titleList.clear()
        curr_title = self.ui.game_table.selectedItems()[0].text()
        self.ui.titleList.addItem(curr_title)

if __name__ == "__main__":
    app = 0 #clear Qt instance in spyder
    app = QApplication(sys.argv)
    window = steam_App()
    window.show()
    sys.exit(app.exec_())

