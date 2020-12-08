import sys
import psycopg2
import pandas as pd

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
import pickle

# Create temp table for scores
#CREATE TABLE temp_score
#select a.appid, a.title, a.type, a.is_multiplayer, a.price, 
#((a.rating*0.6 + (log(temp_purchased.purchases) / (datediff('2017/01/01 00:00:00', a.release_date)/365)* 0.3) + 
#  (log(if(sum(g.playtime_forever) = 0, 1, sum(g.playtime_forever))) /(datediff('2017/01/01 00:00:00', a.release_date)/365)* 0.1))/70) as score
#from games_2 g JOIN app_id_info a on g.appid = a.appid join temp_purchased on temp_purchased.appid = a.appid
#group by appid
#order by score desc;

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
                self.ax.text(rect.get_x() + rect.get_width() / 2., 5, '%d' % int(height), ha='center',
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
        self.cosine_sim = pd.read_pickle(r'co_sim')
        self.df = pd.read_pickle('final_df_bag', compression='infer')
        
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
        self.ui.priceList.clear()
        self.ui.multiList.clear()
        self.ui.busi_gen.clear()
        self.ui.busi_gen_2.clear()
        self.ui.rev_games.clear()
        self.ui.rev_dlc.clear()
        op = self.ui.optionList.currentText()
        if (self.ui.optionList.currentIndex()>=0):
            if op == "All Games" or op == "Best Ratings" or op == "Price Points" or op == "Most Purchased" or op == 'Game Recommendation: User':
                self.ui.busi_pan.setStyleSheet("background: transparent")
                self.ui.busi_gen.setStyleSheet("background: transparent")
                self.ui.busi_gen_2.setStyleSheet("background: transparent")
                self.ui.rev_games.setStyleSheet("background: transparent")
                self.ui.rev_dlc.setStyleSheet("background: transparent")
                self.ui.gen_lab.setText("")
                self.ui.gen_lab2.setText("")
                self.ui.rev_lab_games.setText("")
                self.ui.rev_lab2.setText("")
                self.ui.gen_lab.setStyleSheet("background: transparent")
                self.ui.gen_lab2.setStyleSheet("background: transparent")
                self.ui.rev_lab_games.setStyleSheet("background: transparent")
                self.ui.rev_lab2.setStyleSheet("background: transparent")
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
                    results4 = ("Yes", "No")
                    for item in results4:
                        self.ui.multiList.addItem(item)
                    self.ui.multiList.setCurrentIndex(-1)
                    
                except:
                    print("Query failed!")
            elif op == 'Game Recommendation: Business':
                self.ui.busi_pan.setStyleSheet("background-color: rgb(100,100,100)")
                self.ui.busi_gen.setStyleSheet("background: rgb(200,200,200)")
                self.ui.busi_gen_2.setStyleSheet("background: rgb(200,200,200)")
                self.ui.rev_games.setStyleSheet("background: rgb(200,200,200)")
                self.ui.rev_dlc.setStyleSheet("background: rgb(200,200,200)")
                self.ui.gen_lab.setText("Genres in Top 10 Games")
                self.ui.gen_lab.setStyleSheet("color: white; background: rgb(100,100,100); font: 8pt 'Lucida Sans';")
                self.ui.gen_lab2.setText("Genres in Top 10 DLCs")
                self.ui.gen_lab2.setStyleSheet("color: white; background: rgb(100,100,100); font: 8pt 'Lucida Sans';")
                self.ui.rev_lab_games.setText("Revenue from Top 10 Games:")
                self.ui.rev_lab_games.setStyleSheet("color: white; background: rgb(100,100,100); font: 8pt 'Lucida Sans';")
                self.ui.rev_lab2.setText("Revenue from Top 10 DLCs:")
                self.ui.rev_lab2.setStyleSheet("color: white; background: rgb(100,100,100); font: 8pt 'Lucida Sans';")
                self.getBusiRecs()
                
            else:
                pass
        else:
            pass
    
    # helper class for games
    def getGamesHelper(self):
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
        if (self.ui.multiList.currentIndex() > -1):
            multi = self.ui.multiList.currentText()
            if multi == "Yes":
                multi_str = "and a.Is_Multiplayer = '1' "
            elif multi == "No":
                multi_str = "and a.Is_Multiplayer = '0' "
        elif (self.ui.multiList.currentIndex() == -1):
            multi_str = ""
        
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
        
        self.getGames(genre_str, type_str, price_str, multi_str)
        
    # function to get games from sql server based on options selected
    def getGames(self, gen, type_sel, price, multi):
        #self.ui.searchBar.setPlaceholderText("")
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
                            multi + \
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
                            multi + \
                            "group by a.Title " + \
                            "order by a.Rating desc;"
                            
                graph_str = "select distinct a.Title, a.Rating, a.Price, a.Type, g.Genre " + \
                            "from app_id_info a, games_genres g " + \
                            "where a.appid = g.appid and " + \
                            "a.Rating > 70 " + \
                            gen + \
                            type_sel + \
                            price + \
                            multi + \
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
                temp_str = "select t.title, t.purchases, t.Rating, a.Price, a.Type, g.Genre " + \
                            "from temp_purchased t join games_genres g on t.appid = g.appid " + \
                            "join app_id_info a on a.appid = t.appid " + \
                            gen + \
                            type_sel + \
                            price + \
                            multi + \
                            "group by t.appid " + \
                            "order by purchases desc;"
                
                graph_str = "select a.title, a.purchases, a.Rating, a.Price, a.Type, g.Genre " + \
                            "from temp_purchased a, games_genres g " + \
                            "where a.appid = g.appid " + \
                            gen + \
                            type_sel + \
                            price + \
                            multi + \
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
                            multi + \
                            'group by a.Price order by a.Price asc;'
                
                graph_str = 'select a.Price , count(a.Price) as numGamesPriced ' + \
                            'from app_id_info a, games_genres g ' + \
                            'where a.appid = g.appid and ' + \
                            'a.Price < 100 ' + \
                            gen + \
                            type_sel + \
                            price + \
                            multi + \
                            'group by a.Price order by a.Price asc;'

                results = self.executeQuery(temp_str)
                self.insertGamesPrice(results, graph_str)
                
            elif criteria == "Game Recommendation: User":
                temp_str = 'select a.title, a.Price , a.rating ' + \
                            'from app_id_info a, games_genres g ' + \
                            'where a.appid = g.appid ' + \
                            gen + \
                            type_sel + \
                            price + \
                            multi + \
                            'group by a.title order by a.rating desc ' + \
                            'limit 20;'
                
                graph_str = 'select a.title, a.Price , a.rating ' + \
                            'from app_id_info a, games_genres g ' + \
                            'where a.appid = g.appid ' + \
                            gen + \
                            type_sel + \
                            price + \
                            multi + \
                            'group by a.title order by a.rating desc ' + \
                            'limit 10;'

                results = self.executeQuery(temp_str)
                self.insertGamesUser(results, graph_str)

        except:
            pass
    
    def getBusiRecs(self):
        dlc_str = "select appid, price*purchases as rev from temp_purchased where type = 'dlc' group by appid order by rev desc limit 10;"
        game_str = "select appid, price*purchases as rev from temp_purchased where type = 'game' group by appid order by rev desc limit 10;"
    
        dlc_gen = self.executeQuery(dlc_str)
        game_gen = self.executeQuery(game_str)
        dlc_total = 0
        game_total = 0
        gz_gen = []
        dl_gen = []
        tot_gen = []
        tot_dlc_gen = []
        
        for i, j in dlc_gen:
            dlc_total = dlc_total + j
            dl_gen.append(i)
        for i, j in game_gen:
            game_total = game_total + j
            gz_gen.append(i)
        
        for x in gz_gen:
            z = self.executeQuery("select genre from games_genres where appid = '" + str(x) + "';")
            for p in z:
                if p[0] not in tot_gen:
                    tot_gen.append(p[0])

        for x in dl_gen:
            z = self.executeQuery("select genre from games_genres where appid = '" + str(x) + "';")
            for p in z:
                if p[0] not in tot_dlc_gen:
                    tot_dlc_gen.append(p[0])

        id_list = dl_gen + gz_gen
        all_game = []
        for x in id_list:
            out_games = self.executeQuery("select title, rating, type, price*purchases from temp_purchased where appid = '" + str(x) + "' group by title order by price*purchases desc;")
            all_game.append(out_games[0])
        
        
        self.ui.rev_games.addItem("$" + str(game_total))
        self.ui.rev_dlc.addItem("$" + str(dlc_total))
        for w in tot_gen:
            self.ui.busi_gen.addItem(w)
        for w in tot_dlc_gen:
            self.ui.busi_gen_2.addItem(w)
        self.insertBusiRec(all_game)
        self.graphBusi(tot_gen + tot_dlc_gen)
        #print(dl_gen)
    
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
            #pass
        #self.bestRating()
        
    def insertBusiRec(self, results):
        try:
            if (len(results) > 0):
                style = "::section {""background-color: #f3f3f3; }"
                self.ui.outputTable.horizontalHeader().setStyleSheet(style)
                self.ui.outputTable.setColumnCount(len(results[0]))
                self.ui.outputTable.setRowCount(len(results))
                self.ui.outputTable.setHorizontalHeaderLabels(['Title', 'Rating', 'Type', 'Revenue'])
                currentRowCount = 0
                for row in results:
                    for colCount in range (0,len(results[0])):
                        self.ui.outputTable.setItem(currentRowCount,colCount,QTableWidgetItem(str(row[colCount])))
                    currentRowCount += 1
                #self.ui.outputTable.resizeColumnsToContents()
                
            else:
                self.ui.outputTable.setColumnCount(4)
                self.ui.outputTable.setHorizontalHeaderLabels(['Title', 'Rating', 'Type', 'Revenue'])
            
            self.ui.outputTable.setColumnWidth(0, 200)
            self.ui.outputTable.setColumnWidth(1, 50)
            self.ui.outputTable.setColumnWidth(2, 60)
            self.ui.outputTable.setColumnWidth(3, 60)

        
        except:
            print("Query 4 failed!")
            #pass
        
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
            print("Query 4 failed!")
            #pass
        #self.bestRating()
    
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
            print("Query 4 failed!")
            
    def insertGamesUser(self, results, graph_str):
        try:
            if (len(results) > 0):
                style = "::section {""background-color: #f3f3f3; }"
                self.ui.outputTable.horizontalHeader().setStyleSheet(style)
                self.ui.outputTable.setColumnCount(len(results[0]))
                self.ui.outputTable.setRowCount(len(results))
                self.ui.outputTable.setHorizontalHeaderLabels(['Title', 'Price', 'Rating'])
                currentRowCount = 0
                for row in results:
                    for colCount in range (0,len(results[0])):
                        self.ui.outputTable.setItem(currentRowCount,colCount,QTableWidgetItem(str(row[colCount])))
                    currentRowCount += 1
                #self.ui.outputTable.resizeColumnsToContents()
                
            else:
                self.ui.outputTable.setColumnCount(3)
                self.ui.outputTable.setHorizontalHeaderLabels(['Title', 'Price', 'Rating'])
            
            self.ui.outputTable.setColumnWidth(0, 300)
            self.ui.outputTable.setColumnWidth(1, 60)
            self.ui.outputTable.setColumnWidth(2, 60)
            
            graph_results = self.executeQuery(graph_str)
            self.userGraph(graph_results)
            
        except:
            print("Query 4 failed!")
            
    # function for clear filter button
    def clearFilter(self):
        self.ui.genreList.clearSelection()
        self.ui.typeList.clearSelection()
        self.ui.priceList.setCurrentIndex(-1)
        self.ui.multiList.setCurrentIndex(-1)
           
    # set up ratings graph
    def bestRating(self, results):
        names = []
        ratings = []

        for (name, rating, price, type, genre) in results:
            names.append(name)
            ratings.append(rating)
        
        chart = Canvas(self)
        chart.title = "Best Rated Games"
        chart.xlabel = "Game Name"
        chart.ylabel = "Rating"
        chart.subtitle = "2016"
        chart.x = names
        chart.y = ratings
        chart.plot_chart()
    
    def userGraph(self, results):
        titles = []
        ratings = []
        prices = []

        for (name, price, rating) in results:
            titles.append(name)
            ratings.append(rating)
            prices.append(price)
        
        chart = Canvas(self)
        chart.title = "User Recommendations"
        chart.xlabel = "Game Name"
        chart.ylabel = "Rating"
        chart.subtitle = "2016"
        chart.x = titles
        chart.y = ratings
        #chart.price = prices
        chart.plot_chart()
    
    # set up most purhcased graph
    def mostPurchased(self, results):
        names = []
        purchases = []
    
        for (name, purchase, rating, price, type, genre) in results:
            names.append(name)
            purchases.append(purchase)
        
        chart = Canvas(self)
        chart.title = "Most Purchased Games"
        chart.xlabel = "Game Name"
        chart.ylabel = "Purchases"
        chart.subtitle = "2016"
        chart.x = names
        chart.y = purchases
        chart.plot_chart()
        #self.ui.mplWindow.setItem(chart) 
        
    def graphBusi(self, results):
        all_gen = []
        for x in results:
            if x not in all_gen:
                all_gen.append(x)
        
        sums = []        
        
        for genre in all_gen:
            some = self.executeQuery("select sum(t.purchases*t.price) from games_genres g, temp_purchased t where g.appid = t.appid and g.genre = '" + genre +"';")
            sums.append(some[0][0])
        
        print(sums)
        print(all_gen)
        chart = Canvas(self)
        chart.title = "Revenues per Genre"
        chart.xlabel = "Genre"
        chart.ylabel = "Revenue"
        chart.subtitle = "2016"
        chart.x = all_gen
        chart.y = sums
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
        
        chart = Canvas(self)
        chart.title = "Game Price Points"
        chart.xlabel = "Prices"
        chart.ylabel = "Number of Games"
        chart.subtitle = "2016"
        chart.x = prices
        chart.y = counts
        chart.avg = priceTotal/numItems
        chart.scatterPlot()
        #self.ui.mplWindow.setItem(chart)
    
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
            print("fail")
          
    # game statitstic information
    def gameStat(self):
        self.ui.titleList.clear()
        curr_title = self.ui.game_table.selectedItems()[0].text()
        self.ui.titleList.addItem(curr_title)
        self.ui.rankList.clear()
        self.ui.statList.clear()
        
        
        stat_str = "select t.title, t.price, t.type, t.is_multiplayer, t.score, row_number() over ( order by t.score desc) as 'RowNumber' " + \
                    "from temp_score t, games_genres g " + \
                    "where t.appid = g.appid " + \
                    "group by t.title " + \
                    "order by t.score desc;"
  
        try:
            results = self.executeQuery(stat_str)
            df = pd.DataFrame(results, columns=('title', 'price', 'type', 'multi', 'score', 'rank'))
            temp = df[df['title']==curr_title]['rank'].to_string(index=False)
            try: 
                int(temp)
                str(temp)    
                temp = self.rankClean(temp)
            except:
                temp = '-'
            self.ui.rankList.addItem(temp + " / " + str(len(df)))
        except:
            self.ui.rankList.addItem('NA')
        
        try:
            price = df[df['title']==curr_title]['price'].to_string(index=False)
            if price == 'Series([], )':
                price = 'NA'
            else:
                pass
        except:
            price = 'NA'
        game_str = "Price: $" + price + " | "
        
        self.genreStat(curr_title, game_str)
        self.playStat(curr_title)
        self.gameRecs(curr_title)
       
    # rank by genre
    def genreStat(self, title, game_str):
        self.ui.genList.clear()
        try:
            gen_stat = self.executeQuery("select g.genre from app_id_info a, games_genres g where a.appid = g.appid and a.title = '" + title + "' LIMIT 1;")      
        except:
            gen_stat = []
        if len(gen_stat) > 0:
            genre = "and g.Genre = '" + gen_stat[0][0] + "' "
        else:
            genre = ""
        gen_str = "select t.title, t.score, row_number() over ( order by t.score desc) as 'RowNumber' " + \
                    "from (select t.title, t.score " + \
                    "from temp_score t, games_genres g where t.appid = g.appid " + \
                    genre + \
                    ") t " + \
                    "group by t.title " + \
                    "order by t.score desc;;"
                    
        results = self.executeQuery(gen_str)
        df = pd.DataFrame(results, columns=('title', 'score', 'rank'))
        temp = df[df['title']==title]['rank'].to_string(index=False)
        try: 
            int(temp)
            str(temp) 
            temp = self.rankClean(temp)
        except:
            temp = '-'
        self.ui.genList.addItem(temp + " / " + str(len(df)))
        
        try:
            game_str = "Genre: " + gen_stat[0][0] + " | " + game_str
        except:
            game_str = "NA"
        self.revStat(title, game_str)
        
    # rank by revenue
    def revStat(self, title, game_str):
        self.ui.revList.clear()
        rev_stat = self.executeQuery("select title, (price*purchases) as rev, row_number() over ( order by price*purchases desc) as 'RowNumber' from temp_purchased group by title order by rev desc;")      

        df = pd.DataFrame(rev_stat, columns=('title', 'revenue', 'rank'))
        temp = df[df['title']==title]['rank'].to_string(index=False)
        try: 
            int(temp)
            str(temp)  
            temp = self.rankClean(temp)              
        except:
            temp = '-'
        self.ui.revList.addItem(temp + " / " + str(len(df)))
        
        revenue = df[df['title']==title]['revenue'].to_string(index=False)
        if revenue == 'Series([], )':
            revenue = 'NA'
        else:
            pass
        game_str = game_str + "Revenue: $" + revenue + " | "
        self.ui.statList.addItem(game_str)
    
    # rank by playtime
    def playStat(self, title):
        self.ui.playList.clear()
        play_stat = self.executeQuery("select title, playtime, row_number() over ( order by playtime desc) as 'RowNumber' from temp_score group by title order by playtime desc;")      

        df = pd.DataFrame(play_stat, columns=('title', 'playtime', 'rank'))
        temp = df[df['title']==title]['rank'].to_string(index=False)
        try: 
            int(temp)
            str(temp) 
            temp = self.rankClean(temp)               
        except:
            temp = '-'
        self.ui.playList.addItem(temp + " / " + str(len(df)))
        
        pt = df[df['title']==title]['playtime'].to_string(index=False)
        if pt == 'Series([], )':
            pt = 'NA'
        else:
            pass
        game_str = "Playtime: " + pt + " | "
        
        self.purchaseStat(title, game_str)
    
    # rank by downloads
    def purchaseStat(self, title, game_str):
        self.ui.downList.clear()
        down_stat = self.executeQuery("select title, purchases, row_number() over ( order by purchases desc) as 'RowNumber' from temp_purchased group by title order by purchases desc;")      

        df = pd.DataFrame(down_stat, columns=('title', 'purchases', 'rank'))
        temp = df[df['title']==title]['rank'].to_string(index=False)
        try: 
            int(temp)
            str(temp) 
            temp = self.rankClean(temp)            
        except:
            temp = '-'
        self.ui.downList.addItem(temp + " / " + str(len(df)))
        
        pur = df[df['title']==title]['purchases'].to_string(index=False)
        if pur == 'Series([], )':
            pur = 'NA'
        else:
            pass
        game_str = game_str + "Downloads: " + pur
        self.ui.statList.addItem(game_str)
        
    # clean up rankings
    def rankClean(self, rank):
        if rank[-2:] == '11':
            rank = rank + "th"
        elif rank[-1] == '1':
            rank = rank + "st"
        elif rank[-2:] == '12':
            rank = rank + "th"
        elif rank[-1] == '2':
            rank = rank + "nd"
        elif rank[-2:] == '13':
            rank = rank + "th"
        elif rank[-1] == '3':
            rank = rank + "rd"
        else:
            rank = rank + "th"
        return rank
        
    def gameRecs(self, title):
        self.ui.topCat.clear()
        ls = "select appid from app_id_info where title = '" + title + "';"
        results = self.executeQuery(ls)
        #print(results[0][0])
        
        recs = self.recommendations(results[0][0])
        title_list = []
        for game in recs:
            results = self.executeQuery("select title from app_id_info where appid = '" + str(game) + "';")    
            title_list.append(results[0][0])
        
        for item in title_list:
            self.ui.topCat.addItem(item)
        #print(title_list)
        
        return
            
    def recommendations(self, appid):
    
        indices = pd.Series(self.df.index)
        
        recommended = []
        idx = indices[indices == appid].index[0]
        
        score_series = pd.Series(self.cosine_sim[idx]).sort_values(ascending=False)
        
        top_15 = list(score_series.iloc[0:14].index)
        for i in top_15:
            recommended.append(list(self.df.index)[i])
        
        if appid in recommended:
            recommended.remove(appid)
        else: 
            pass
        return recommended

if __name__ == "__main__":
    app = 0 #clear Qt instance in spyder
    app = QApplication(sys.argv)
    window = steam_App()
    window.show()
    sys.exit(app.exec_())