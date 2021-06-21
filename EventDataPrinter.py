from EventDataFetcher import GatyaFetcher,StageFetcher,ItemFetcher

language = input('Enter Version (en/kr/jp/tw)\n')
if language not in ['en','kr','jp','tw']:
  language = 'en'

# M = ignore all events lasting longer than a month
# Y = ignore all events that ended yesterday or earlier
# To enter multiple filters just type all their characters (e.g. MY)
filters = list(input('Enter Filters\n'))

gf = GatyaFetcher('en',['M'])
gf.fetchRawData()
gf.readRawData()
gf.printGatya()

sf = StageFetcher('en',['M'])
sf.fetchRawData()
sf.readRawData()
sf.groupData()
s1 = sf.getStageData()

itf = ItemFetcher('en',['M'])
itf.fetchRawData()
itf.readRawData()
itf.groupData()
s2 = itf.getStageData()

sf.printStages(s1[0]+s2[0],s1[1]+s2[1])

input()