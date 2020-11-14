import mysql.connector
import matplotlib.pyplot as plt
import numpy as np
from textwrap import wrap

LIMIT = 11

db = mysql.connector.connect(user='root', password='Eggroll239!',host='127.0.0.1',database='newsteam', port=3309)
cur = db.cursor()

def main():

  print(cur)

  showBestRatings()
  #showMostPurchased()
  #showPricePoints()
  gameRecommendationUser()
  cur.close()



def printMenu():
  print("Which options would you like to view:")
  print("1: Best Ratings")
  print("2: Most Purchased")
  print("3: Game Recommendation: User")
  print("4: Game Recommendation: Business")
  print("5: Price Points")

def userRecGenres():
  cur.execute('select Genre from games_genres group by Genre')
  rows = cur.fetchall()
  count = 1
  userGenres = ""
  userIn = ""
  first = True
  while userIn != "q" and userIn != "quit":
    print("What kind of genres are you looking for?")
    for item in rows:
      if not(str(item[0]) in userGenres):
        print(str(count) + ". " + item[0])
        count += 1

    userIn = input()
    if str(userIn) != "q":
      userIn = int(userIn)
      if userIn > 0 and userIn <= count:
        if first:
          userGenres += 'Genre=\'' + str(item[0]) + '\' '
          first = False
        else:
          userGenres += 'or Genre=\'' + str(item[0]) + '\' '
        count = 1

  return userGenres


def gameRecommendationUser():
  userGenres = userRecGenres()

  if not userGenres:
    userGenres = " Genre=\'Action\' "

  cur.execute('select Title, Rating, Price from app_id_info natural join games_genres where Type=\'game\' and ' + userGenres +' order by Rating desc limit 10')
  rows = cur.fetchall()
  titles = []
  ratings = []
  prices = []

  for (title, rating, price) in rows:
    titles.append(title)
    ratings.append(rating)
    prices.append(price)

  showGraphBar(title,rating, title="Recommended Games", tX="Game Titles", tY="Rating", subT="2016", heightSpacing=1.05, price=prices)



def showPricePoints():
  cur.execute('select Price , count(Price) as numGamesPriced from app_id_info where Price < 100 group by Price order by Price asc')
  rows = cur.fetchall()
  prices = []
  counts = []

  priceTotal = 0
  numItems = 0
  for (price, count) in rows:
    prices.append(price)
    counts.append(count)
    if price > 0:
      numItems += 1
      priceTotal += price


  showScatterPlot(prices,counts,title="Game Price Points", tX="Price", tY="Number of Games", subT="2016", avg= priceTotal/numItems)

def showMostPurchasedContentSelection():
  cur.execute('select Type from app_id_info group by Type')
  rows = cur.fetchall()
  print("What kind of most purchased are you looking for?")
  count = 1
  for item in rows:
    print(str(count) + ". " + item[0])
    count += 1

  return str(rows[int(input()) - 1][0])


def showMostPurchased():

  userInput = showMostPurchasedContentSelection()

  if userInput == None:
    userInput = 'game'


  cur.execute('select Title, count(appid) as purchases from games_2 natural join app_id_info where games_2.appid = app_id_info.appid and Type=\'' + userInput + '\' group by appid order by purchases desc limit ' + str(LIMIT) + ';')
  rows = cur.fetchall()
  names = []
  purchases = []

  for (id, purchase) in rows:
    names.append(id)
    purchases.append(purchase)

  showGraphBar(names,purchases, title="Most Purchased "+userInput.capitalize(), tX= userInput.capitalize() + " Name", tY="Purchases", subT="2016", heightSpacing=1, price=None)


def showBestRatings():
  cur.execute('select * from app_id_info where Rating > 70 and type = \'game\'order by Rating desc limit ' + str(LIMIT) + ';')
  rows = cur.fetchall()
  names = []
  ratings = []

  for (id, name, type, price, date, rating, rAge, mult) in rows:
    names.append(name)
    ratings.append(rating)

  showGraphBar(names,ratings, title="Best Rated Games", tX="Game Name", tY="Rating", subT="2016", heightSpacing=1.05, price=None)


def showScatterPlot(x,y, title, tX, tY, subT, avg):
  x = np.array(x)
  y = np.array(y)
  plt.scatter(x, y)
  plt.ylabel(tY)
  plt.xlabel(tX)
  plt.title(title)
  plt.suptitle(subT)

  avg = "{:.2f}".format(avg)

  plt.gcf().text(0.7, 0.7, "avg = " + str(avg) + "\nmin = " + str(x[1])+ "\nmax = " + str(x[-1]) , fontsize=14)

  plt.show()


def showGraphBar(x,y, title, tX, tY, subT, heightSpacing, price):
  x = np.array(x)
  y = np.array(y)
  fig, ax = plt.subplots()
  rects = ax.bar(x,y)
  plt.bar(x,y)
  plt.ylabel(tY)
  plt.xlabel(tX)
  plt.title(title)
  plt.suptitle(subT)

  # shows the value of the bar
  count = 0
  for rect in rects:
    height = rect.get_height() - 4
    ax.text(rect.get_x() + rect.get_width() / 2., heightSpacing * height,'%d' % int(height),ha='center', va='bottom')
    if not (price is None):
      ax.text(rect.get_x() + rect.get_width() / 2., 1, '%d' % int(height), ha='center',
              va='bottom')


  if x.size > 1:
    namesSpaced = ['\n'.join(wrap(i, 12)) for i in x]
    plt.xticks(x, namesSpaced, rotation=90)
    fig.tight_layout()






  #plt.tight_layout()
  plt.show()

main()

