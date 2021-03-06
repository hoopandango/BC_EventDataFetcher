from EventDataFetcher import GatyaFetcher,StageFetcher,ItemFetcher
from datetime import datetime as dt
import time
from pprint import pprint # Please use this, whoever from the future is trying to debug this spaghetti.

lg = 'jp'
fl = 'NY'

lg = input('Enter Version (en/kr/jp/tw)\n')
if lg not in ['en','kr','jp','tw']:
  pass

# M = ignore all events lasting longer than a month
# Y = ignore all events that ended yesterday or earlier
# N = basically N but better
# To enter multiple filters just type all their characters (e.g. NY)
filters = list(input('Enter Filters (Enter NY if you don\'t know what this is)\n'))
fl = []
for ch in 'MYN':
  if ch in filters:
    fl+=ch

try:
  d0 = dt.strptime(input('Enter Starting Date or leave blank to use today (e.g. 20210403)\n'),'%Y%m%d')
  gf,sf,itf = GatyaFetcher(lg,fl,d0),StageFetcher(lg,fl,d0),ItemFetcher(lg,fl,d0)
except:
  print('Date entered invalid or left blank. Using today as the pivot date.')
  gf,sf,itf = GatyaFetcher(lg,fl),StageFetcher(lg,fl),ItemFetcher(lg,fl)


gf.fetchRawData()
gf.readRawData()
gf.printGatya()

sf.fetchRawData()
sf.readRawData()
sf.groupData()
s1 = sf.getStageData()
#print(sf.finalStages)

itf.fetchRawData()
itf.readRawData()
itf.groupData()
s2 = itf.getStageData()

sf.printStages(s1[0]+s2[0],s1[1]+s2[1])

itf.printItemData()

"""
sf.fetchRawData()
sf.readRawData()
sf.groupData()
#pprint(sf.refinedStages)
"""
sf.printFestivalData()

input()
