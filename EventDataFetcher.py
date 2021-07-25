import csv
import json
import urllib.request
import html
import regex as re
import datetime
from Catbot import Catunits as cat
from operator import itemgetter
import os

fl = 'LocalData\\' # Set to '' if keeping data files in same folder
groupable_events = ['Seeing Red','Tag Arena','Dark','Duel','(Baron)','Citadel']
weekdays = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']

with open(fl+'EventGroups.json', encoding='utf-8') as f:
	f = f.read()
	y = json.loads(f)
	event_groups = y

class UniversalParsers:
	eventNames = {}
	itemdata = []


	with open(fl+'Stages.csv', 'r', encoding='utf-8') as csvfile:
		reader = csv.reader(csvfile, delimiter=",")
		for row in reader:
			eventNames[row[0]] = row[1][1:]
	
	with open(fl+'Events.csv', 'r', encoding='utf-8') as csvfile:
		reader = csv.reader(csvfile, delimiter=",")
		for row in reader:
			eventNames[row[0]] = row[1]

	with open(fl+'DropItemData.csv', 'r', encoding = 'utf-8', newline='') as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			itemdata.append(row)

	@staticmethod
	def fancyDate(datesall):
		toret = "- "
		for dates in zip(datesall[0::2],datesall[1::2]):
			
			if (dates[1] - dates[0]).days > 365:   # Forever Events
				toret += f"{dates[0].strftime('%d %b').lstrip('0')}~..."

			elif dates[0].month == dates[1].month:   # Events that don't cross months
				if dates[0].day == dates[1].day:   # Events that only last one day or less
					toret += dates[1].strftime('%d %b').lstrip('0')
				else:
					toret += '~'.join([dates[0].strftime('%d').lstrip('0'),dates[1].strftime('%d %b').lstrip('0')])

			else:  # Events that cross months
				toret += '~'.join([x.strftime('%d %b').lstrip('0') for x in dates])
		
			toret += ', '

		return toret[:-2] + ": "

	@staticmethod
	def fancyTimes(timesall):
		toret = ""
		if len(timesall) == 0:
			return "All Day"
		for time in timesall:
			if(time['end'].hour == 23 and time['start'].hour == 0): 
				return "All Day"
			toret += f"{time['start'].strftime('%I%p').lstrip('0')}~{time['end'].strftime('%I%p').lstrip('0')}"
			toret += ', '

		return toret[:-2]
		

	@staticmethod
	def areValidDates(dates,filters,date0 = datetime.datetime.today()):
		if len(filters) > 0:
			if 'N' in filters:
				if ((dates[1] - dates[0]).days > 31 and not (dates[0]-date0).days >= 1):
					return False
			elif 'M' in filters:
				if (dates[1] - dates[0]).days > 31:  # If event lasts longer than a month
					return False
			if 'Y' in filters:  
				if (date0-dates[0]).days > -1:  # If event started today or earlier
					return False
		if (date0 - dates[1]).days > 365:  # Default Filter - Ignore (most) discontinued events
			return False
		return True

	@classmethod
	def getdates(cls,data):
		return [cls.formatDate(data[0]+data[1]),cls.formatDate(data[2]+data[3])]

	@staticmethod
	def getversions(data):
		return data[4], data[5]

	@staticmethod
	def formatDate(s):
		return datetime.datetime.strptime(s, '%Y%m%d%H%M')
	
	@classmethod
	def getEventName(cls,ID):
		try:
			name = cls.eventNames[str(ID)]
			if (25000 > int(ID) > 24000 or 28000 > int(ID) > 27000) and 'Baron' not in name:
				name += ' (Baron)'
			return name
		except:
			return "Unknown"
	
	@classmethod
	def getItem(cls,ID):
		for row in cls.itemdata:
			if int(row[0]) == int(ID):
				return row[1]
		return 'Unknown'

class GatyaParsers(UniversalParsers):
	def __init__():
		UniversalParsers.__init__()

	aliases = {'The Almighties: The Majestic Zeus':'Almighties','The Nekoluga Family':'Nekolugas','The Dynamites':'Dynamites','Ancient Heroes: Ultra Souls Event':'Ultra Souls','Sengoku Wargods Vajiras Event':'Vajiras'}

	default_units = {"G":"Cutter Cat","N":"Neneko","R":"Freshman Cat Jobs"}
	default_units = {int(cat.getUnitCode(y,6)[0]/3):x for (x,y) in default_units.items()}

	guessing_units = {"Best of the Best":"Li'l Valkyrie","Neo Best of the Best":"Li'l Valkyrie Dark","DynastyFest":"Tyrant Cat"}
	guessing_units = {int(cat.getUnitCode(y,6)[0]/3):x for (x,y) in guessing_units.items()}

	gatyaInfo = []
	gatyaNames = []
	gib = []

	with open(fl+'GatyaData.csv', encoding='utf-8') as f:
		rows = csv.reader(f)
		for row in rows:
			gatyaInfo.append(row)
	
	with open(fl+'gatyasetnames.json', encoding='utf-8') as f:
		f = f.read()
		y = json.loads(f)
		gatyaNames = y
	
	with open(fl+'Gatyaitembuy.csv', encoding = 'utf-8', newline='') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			gib.append(row)


	@staticmethod
	def getpage(banner):
		p = banner[8]
		if p == "0":
			return "Cat Capsule" #Normal, lucky, G, catseye, catfruit, etc : uses GatyaDataSetN1.csv
		if p == "1":
			return "Rare Capsule" #Rare, platinum : uses GatyaDataSetR1.csv

		return "Event Capsule" #Some other page like bikkuri choco shit, etc, or some old-ass banners that don't exist now idk

	@staticmethod
	def getValueAtOffset(banner, i): #i is the column ID for First Slot banners
		slot = int(banner[9])-1
		offset = 15*slot #Second slot data is 15 columns after first slot, and so on
		return banner[i + offset]

	@staticmethod
	def getGatyaRates(banner):
		rates = []
		for i in range(5):
			rates.append(GatyaParsers.getValueAtOffset(banner, 14 + 2*i)) #14,16,18.20,22
		return rates

	@staticmethod
	def getGatyaG(banner):
		G = []
		for i in range(5):
			G.append(GatyaParsers.getValueAtOffset(banner, 15 + 2*i)) #15,17,19,21,23
		return G
	
	@classmethod
	def guessGatyaName(cls,ID):
		toret = None
		for i in cls.guessing_units:
			if str(i) in cls.gatyaInfo[int(ID)]:
				toret = cls.guessing_units[i]
		if toret:
			return toret + ' (Guessed)'
		raise ValueError('Not Found')

	@classmethod
	def getGatyaName(cls,ID):
		def fetchGatyaName(ID):
			'''  Reading from Local Data, not using because this has untranslated gatya banners and Unknown Sets, but might improve this later.
			try:
				return cls.gatyaNames[str(ID).zfill(3)] if not 'Set Name Unknown' == cls.gatyaNames[str(ID).zfill(3)] else 'Untitled'
			except:
				pass
			'''
			try:  # Get Name from PONOS site
				gatyaurl = 'http://ponos.s3.dualstack.ap-northeast-1.amazonaws.com/information/appli/battlecats/gacha/rare/en/R%i.html'%(int(ID))
				uf = urllib.request.urlopen(gatyaurl)
				tex = uf.read().decode("utf8")
				uf.close()
				title = html.unescape(re.search('<h2>(.*)</h2>', tex).group(1))
				return re.sub('<span.*?</span>', '', title, flags=re.DOTALL)
			except:
				pass
			'''  Can keep this, but it's slower than PONOS site.
			try:	# Get Name from feanor site 
				gatyaurl = 'https://thanksfeanor.pythonanywhere.com/gatya/%i'%(int(ID))
				uf = urllib.request.urlopen(gatyaurl)
				tex = uf.read().decode("utf8")
				uf.close()
				name = html.unescape(re.search('<h1 style="text-align: center;">(.*)</h1>', tex).group(1))
				if name != 'Set Name Unknown':
					return name
			except:
				pass
			'''
			try:  # Guess Gatya name
				return cls.guessGatyaName(ID) 
			except:
				pass

			return 'Untitled'
		
		title = fetchGatyaName(ID)
		title = title.replace('Rare Cat Capsule Event','').replace('Collab Capsules','').strip().title()
		if title in cls.aliases.keys():
			title = cls.aliases[title]
		return title

	@classmethod
	def printGatyaUnitsIn(cls,ID):
		x = cls.gatyaInfo[int(ID)]
		for i in x:
			try:
				name = cat.getnamebycode(3*int(i))
				if name:
					print(name,end=', ')
			except:
				pass
		print()

	@classmethod
	def getExclusives(cls,ID):
		try:
			toret = []
			for i in cls.default_units:
				if str(i) in cls.gatyaInfo[int(ID)]:
					toret.append(cls.default_units[i])
			return toret
		except:
			return []

	@classmethod
	def severToItem(cls,ID):
		for row in cls.gib:
			if int(row['SeverID']) == int(ID):
				return int(row['stageDropItemID'])
		return -1

	@classmethod
	def getExtras(cls,data):
		toret = []
		extras = int(cls.getValueAtOffset(data,13))
		severID = (extras >> 4) & 1023
		itemID = cls.severToItem(severID) # do stuff here
		if extras & 4:
			toret.append('S')  # Step-up
		if extras & 16384:
			toret.append('P')  # Platinum Shard
		if not extras & 8:
			return toret # No item drops
		if cls.getItem(itemID) == 'Lucky Ticket':
			toret.append('L')  # Has lucky ticket
		return toret

class StageParsers(UniversalParsers):
	def __init__():
		UniversalParsers.__init__()

	@staticmethod
	def formatTime(t):
		if t == "2400":
			t = "2359"
		if t == "0":
			t = "0000"
		if len(t) == 3:  #fixes time if hour is < 10am
			t = '0' + t
		dt = datetime.datetime.strptime(t, '%H%M')
		return datetime.time(dt.hour,dt.minute)

	@staticmethod
	def formatMDHM(s,t):
		if t == "2400":
			t = "2359"
		if t == "0":
			t = "0000"
		if len(s) == 3:  # fixes date if month isn't nov or dec
			s = '0' + s

		return datetime.datetime.strptime(s+t, '%m%d%H%M')
	
	@staticmethod
	def binaryweekday(N):
		list_to_return = [int(x) for x in list(bin(N))[2:][::-1]]
		while len(list_to_return)<7:
			list_to_return.append(0)
		return list_to_return

	@classmethod
	def yearly(cls,data):
		numberOfPeriods = int(data[7])
		n = 8
		output = [dict() for x in range(numberOfPeriods)]
		IDs = []
		for i in range(numberOfPeriods):
			
			times, n = int(data[n]), n+1
			output[i]["times"] = [dict() for x in range(times)]
			
			for j in range(times):
				startDate, n = data[n], n+1
				startTime, n = data[n], n+1
				endDate, n = data[n], n+1
				endTime, n = data[n], n+1
				output[i]["times"][j]["start"] = cls.formatMDHM(startDate,startTime)
				output[i]["times"][j]["end"] = cls.formatMDHM(endDate,endTime)
				if output[i]["times"][j]["end"] < output[i]["times"][j]["start"]:  
					# this means the event ends the next year, like it starts on christmas and lasts for 2 weeks
					output[i]["times"][j]["end"] = output[i]["times"][j]["end"].replace(year=1901)
					
			
			n = n + 3 #trailing zeros
		
		nIDs, n = int(data[n]), n+1
		for k in range(max(nIDs,1)):
			ID, n = int(data[n]), n+1
			if nIDs > 0:
				IDs.append(ID)
				
		return output, IDs

	@classmethod
	def monthly(cls,data):
		numberOfPeriods = int(data[7])
		n = 9
		output = [dict() for x in range(numberOfPeriods)]
		IDs = []
		for i in range(numberOfPeriods):
			
			dates, n = int(data[n]), n+1
			output[i]["dates"] = [""]*int(dates)
			for u in range(int(dates)):
				output[i]["dates"][u], n = data[n], n+1
			
			n = n+1 #Trailing zero
			
			times, n = int(data[n]), n+1
			output[i]["times"] = [dict() for x in range(times)]
			
			
			for j in range(times):
				start, n = data[n], n+1
				end, n = data[n], n+1
				output[i]["times"][j]["start"] = cls.formatTime(start)
				output[i]["times"][j]["end"] = cls.formatTime(end)
		
			nIDs, n = int(data[n]), n+1
			for k in range(nIDs):
				ID, n = int(data[n]), n+1
				if nIDs > 0:
					IDs.append(ID)
				
		return output, IDs

	@classmethod
	def weekly(cls,data):
		numberOfPeriods = int(data[7])
		n = 10
		output = [dict() for x in range(numberOfPeriods)]
		IDs = []
		for i in range(numberOfPeriods):
			
			weekdays, n = cls.binaryweekday(int(data[n])), n+1
			output[i]["weekdays"] = weekdays
			times, n = int(data[n]), n+1
			output[i]["times"] = [dict() for x in range(times)]
			
			for j in range(times):
				start, n = data[n], n+1
				end, n = data[n], n+1
				output[i]["times"][j]["start"] = cls.formatTime(start)
				output[i]["times"][j]["end"] = cls.formatTime(end)
			
			nIDs, n = int(data[n]), n+1
			
			for k in range(max(nIDs,1)):
				ID, n = int(data[n]), n+1
				if nIDs > 0:
					IDs.append(ID)
		
		return output, IDs

	@classmethod
	def daily(cls,data):
		numberOfPeriods = int(data[7])
		n = 11
		output = [dict() for x in range(numberOfPeriods)]
		IDs = []
		for i in range(numberOfPeriods):
			
			times, n = int(data[n]), n+1
			output[i]["times"] = [dict() for x in range(times)]
			
			for j in range(times):
				startTime, n = data[n], n+1
				endTime, n = data[n], n+1
				output[i]["times"][j]["start"] = cls.formatTime(startTime)
				output[i]["times"][j]["end"] = cls.formatTime(endTime)
		
		nIDs, n = int(data[n]), n+1
		for k in range(max(nIDs,1)):
			ID, n = int(data[n]), n+1
			if nIDs > 0:
				IDs.append(ID)
		
		return output, IDs

class ItemParsers(UniversalParsers):
	def __init__():
		UniversalParsers.__init__()
	

class UniversalFetcher:
	def __init__(self,v,f):
		self.ver = v
		self.filters = f
		
	def groupData(self):
		group_history_2 = {}
		finalEvents = []
		sales = []

		def pushEventOrSale(dic):
			if dic['dates'][1].hour == 0:
				dic['dates'][1] -= datetime.timedelta(days=1)
			try:
				if 900 > int(dic['IDs'][0]) > 799:
					sales.append(dic)
					return
			except: 
				pass
			finalEvents.append(dic)
			

		def flushGroup(groupname):
			if not group_history_2[groupname]['visible']:
				return
			pushEventOrSale({
					'dates': group_history_2[groupname]['dates'],
					'schedule': 'permanent',
					'name': groupname
				})
			group_history_2.pop(groupname)

		def needsReset(groupname,event):
			group = group_history_2[groupname]
			if event['name'] not in group['events']:
				return False
			if (event['dates'][0] - group['dates'][1]).days > 3:
				return True
			return False

		def addGroup(group,event):
			group_history_2[group['name']] = {'events':[event['name']],'dates':list(event['dates']),'visible':group['visible']}

		def extendGroup(groupname,event):
			group = group_history_2[groupname]
			group['events'].append(event['name'])
			group['dates'][1] = max(group['dates'][1],event['dates'][1])
			group['dates'][0] = min(group['dates'][0],event['dates'][0])
	
		def groupEvents():
			# Also flattens ungrouped events by ID
			for event in self.refinedStages:
				buffer = []
				for ID in event["IDs"]:
					eventname = StageParsers.getEventName(ID)
					if eventname == 'Unknown':
						continue
					event['name'] = eventname	
					grouped = False
					for group in event_groups:
						if eventname in group['stages']:
							grouped = True
							groupname = group['name']
							if groupname in group_history_2:
								if needsReset(groupname,event):
									flushGroup(groupname)
									addGroup(group,event)
								else:
									extendGroup(groupname,event)
							else:
								addGroup(group,event)
					if not grouped:
						e = event.copy()
						e['IDs'] = [ID]
						buffer.append(e)
				for event in buffer:
					pushEventOrSale(event)
			for groupname in group_history_2.copy():
				flushGroup(groupname)
			self.finalStages = finalEvents
			self.sales = sales
		groupEvents()

class GatyaFetcher(UniversalFetcher):
	def __init__(self,v='en',f=['M'],d0 = datetime.datetime.today()):
		UniversalFetcher.__init__(self,v,f)
		self.rawGatya = []
		self.refinedGatya = []
		self.date0 = d0

	def fetchLocalData(self,date):
		d0 = int(date.strftime('%Y%m%d')+'000000')
		mypath = 'Archive\\en\\gatya\\'
		arr = os.listdir(mypath)
		fname = 0
		for file in arr:
			f = int(file.replace('.tsv',''))
			if f - d0 > 0:
				break
			fname = f
			
		with open(mypath+str(fname)+'.tsv','r', encoding='utf-8') as response:
			lines = response.readlines()
		cr = csv.reader(lines, delimiter="\t")
		for row in cr:
			if len(row) > 1:
				self.rawGatya.append(row)
				if len(row) > 1 and row[1] == "0":
					row[1] = "0000"
				if len(row) > 3 and row[3] == "0":
					row[3] = "0000"

	def fetchRawData(self):		
		if (datetime.datetime.today() - self.date0).days > 60:
			self.fetchLocalData(self.date0)
			return
		url = 'https://bc-seek.godfat.org/seek/%s/gatya.tsv'%(self.ver)
		response = urllib.request.urlopen(url)
		lines = [l.decode('utf-8') for l in response.readlines()]
		cr = csv.reader(lines, delimiter="\t")
		for row in cr:
			if len(row) > 1:
				self.rawGatya.append(row)
				row[1],row[3] = (row[1]+'000')[0:3],(row[3]+'000')[0:3]

	def readRawData(self):
		for banner in self.rawGatya:
			dates = GatyaParsers.getdates(banner)
			if not GatyaParsers.areValidDates(dates,self.filters,self.date0):
				continue
			ID = GatyaParsers.getValueAtOffset(banner, 10)
			name =  GatyaParsers.getGatyaName(ID)

			self.refinedGatya.append({
				"dates": GatyaParsers.getdates(banner),
				"versions": GatyaParsers.getversions(banner),
				"page": GatyaParsers.getpage(banner), #Is it on rare gacha page or silver ticket page
				"slot": banner[9], # affects how to read rest of data
				"Banner_ID": ID, #The ID in the relevant GatyaDataSet csv
				"rates": GatyaParsers.getGatyaRates(banner), #[Normal, Rare, Super, Uber, Legend]
				"Guarantee": GatyaParsers.getGatyaG(banner), #[Normal, Rare, Super, Uber, Legend] - (0:no,1:yes)
				"Text": GatyaParsers.getValueAtOffset(banner, 24),
				"name":name,
				"exclusives": GatyaParsers.getExclusives(ID),
				"extras": GatyaParsers.getExtras(banner)
				})

	def printGatya(self):
		print('```Gatya:')
		for event in self.refinedGatya:
			if 'G' in event['exclusives']:
				event['exclusives'].remove('G')
			if event['rates'][3] in ('10000','9500'):  # Platinum / Legend Ticket Event
				continue
			if event['page'] in ('Rare Capsule','Event Capsule') and int(event['Banner_ID']) > 0:
				gtd = ' (Guaranteed)' if event['Guarantee'][3] == '1' else ''
				gtd += ' (Step-Up)' if 'S' in event['extras'] else ''
				gtd += ' (Lucky Tickets)' if 'L' in event['extras'] else ''
				gtd += ' (Platinum Shard)' if 'P' in event['extras'] else ''
				exclusives = ' ('+')('.join(event['exclusives'])+')' if len(event['exclusives']) > 0 else ''
				name = event['name'] if event['name'] != 'Untitled' else event['Text']
				
				print('%s%s%s%s'%(GatyaParsers.fancyDate(event['dates']),name,gtd,exclusives))

		print('```')

class StageFetcher(UniversalFetcher):
	def __init__(self,v='en',f=['M'], d0 = datetime.datetime.today()):
		UniversalFetcher.__init__(self,v,f)
		self.rawStages = []
		self.refinedStages = []
		self.finalStages = []
		self.sales = []
		self.date0 = d0

	def fetchLocalData(self,date):
		d0 = int(date.strftime('%Y%m%d')+'000000')
		mypath = 'Archive\\en\\sale\\'
		arr = os.listdir(mypath)
		fname = 0
		for file in arr:
			f = int(file.replace('.tsv',''))
			if f - d0 > 0:
				break
			fname = f
			
		with open(mypath+str(fname)+'.tsv','r', encoding='utf-8') as response:
			lines = response.readlines()
		cr = csv.reader(lines, delimiter="\t")
		for row in cr:
			if len(row) > 1:
				self.rawStages.append(row)
				if len(row) > 1 and row[1] == "0":
					row[1] = "0000"
				if len(row) > 3 and row[3] == "0":
					row[3] = "0000"

	def fetchRawData(self):		
		if (datetime.datetime.today() - self.date0).days > 60:
			self.fetchLocalData(self.date0)
			return
		url = 'https://bc-seek.godfat.org/seek/%s/sale.tsv'%(self.ver)
		response = urllib.request.urlopen(url)
		lines = [l.decode('utf-8') for l in response.readlines()]
		cr = csv.reader(lines, delimiter="\t")
		for row in cr:
			if len(row) > 1:
				self.rawStages.append(row)
				row[1],row[3] = (row[1]+'000')[0:4],(row[3]+'000')[0:4]

	def printRawData(self):
		print (self.rawStages)

	def readRawData(self):
		for data in self.rawStages:
			if not StageParsers.areValidDates(StageParsers.getdates(data),self.filters,self.date0):
				continue
			
			#permanent - just ID - all day
			if data[7] == '0':
				self.refinedStages.append({
					"dates": StageParsers.getdates(data),
					"versions": StageParsers.getversions(data),
					"schedule": "permanent", 
					"IDs": [int(x) for x in data[9:9+int(data[8])]]
					})
			#Yearly repeat XY - starts and ends at a date+time
			elif data[8] != '0':
				ydata, yIDs = StageParsers.yearly(data)
				self.refinedStages.append({
					"dates": StageParsers.getdates(data),
					"versions": StageParsers.getversions(data),
					"schedule": "yearly", 
					"data": ydata,
					"IDs": yIDs
					})
			#Monthly repeat X0Y - list of days of month, may have time range
			elif data[9] != '0':
				mdata, mIDs = StageParsers.monthly(data)
				self.refinedStages.append({
					"dates": StageParsers.getdates(data),
					"versions": StageParsers.getversions(data),
					"schedule": "monthly", 
					"data": mdata,
					"IDs": mIDs
					})
			#Weekly repeat X00Y - list of weekdays, may have time ranges
			elif data[10] != '0':
				wdata, wIDs = StageParsers.weekly(data)
				self.refinedStages.append({
					"dates": StageParsers.getdates(data),
					"versions": StageParsers.getversions(data),
					"schedule": "weekly",
					"data": wdata,
					"IDs": wIDs
					})
			#Daily repeat X000Y - list of time ranges every day in interval
			elif data[11] != '0':
				ddata, dIDs = StageParsers.daily(data)
				self.refinedStages.append({
					"dates": StageParsers.getdates(data),
					"versions": StageParsers.getversions(data),
					"schedule": "daily", 
					"data": ddata,
					"IDs": dIDs
					})

	def getStageData(self):
		return (self.finalStages,self.sales)

	def printFestivalData(self):
		permanentLog = []
		for event in self.refinedStages:
			for ID in event['IDs']:
				# Checks come here

				if event['schedule'] == 'permanent' and (ID not in (1028,1059,1124,1155,1078,1007,1006) or ID in permanentLog):
					continue

				if StageParsers.getEventName(ID) == 'Unknown':
					continue

				# Starts printing here
				print(f'```{StageParsers.getEventName(ID)}')

				if event['schedule'] == 'permanent':	
					permanentLog.append(ID)
					# Merges ALL instances of this event!!
					for e in [x for x in self.refinedStages if ID in x['IDs']]:
						print(f"- {e['dates'][0].strftime('%d')}: {e['dates'][0].strftime('%I%p')}~{e['dates'][1].strftime('%I%p')}")
					
				elif event['schedule'] == 'monthly':
					for setting in event['data']:
						if len(setting['times']) == 0:
							print(' - Date '+'/'.join(setting['dates']))
						else:
							print('- Date '+'/'.join(setting['dates'])+ ': ' + f"{setting['times'][0]['start'].strftime('%I%p').lstrip('0')}~{setting['times'][0]['end'].strftime('%I%p').lstrip('0')}")

				elif event['schedule'] == 'daily':
					for setting in event['data']:
						print(f"{StageParsers.fancyDate(event['dates'])}{StageParsers.fancyTimes(setting['times'])}")

				elif event['schedule'] == 'weekly':
					for setting in event['data']:
						print(f" - {'/'.join([weekdays[i] for i,val in enumerate(setting['weekdays']) if val == 1])}: {StageParsers.fancyTimes(setting['times'])}")

				elif event['schedule'] == 'yearly':
					print(f"{StageParsers.fancyDate([event['data'][0]['times'][0]['start'],event['data'][0]['times'][0]['end']])[:-2]}")
				
				# End printing
				print('```')

	def printStages(self, stagedata = 'x',saledata = 'x'):
		def groupBaronsAndOtherStuff(events):			
			for i,event in enumerate(events):
				if any([x in event['name'] for x in groupable_events]):
					for j,e in enumerate(events[i+1:]):
						# Can't use two words because Duel stages
						if (e['name'].split(' ')[0] == event['name'].split(' ')[0] or e['name'].split(' ')[-1] == event['name'].split(' ')[-1]) and e['dates'][1] == event['dates'][1]:   # If they share the same first word and end on the same date
							events.insert(i+1,events.pop(i+j+1))   # Put them together
							break

				
		def dupeCheck(events):
			for i,event in enumerate(events):
				if event['name'] == 'Catfood Discount Reset (30)':
					for j,e in enumerate(events[i+1:]):
						if e['name'] == 'Catfood Discount Reset (750)':
							events[i]['name'] = 'Catfood Discount Reset (30/750)'
							events.pop(i+j+1)
							break
				for j,e in enumerate(events[i+1:]):
					try:
						if e['IDs'] == event['IDs']:
							events[i]['dates'].extend(e['dates'])
							events.pop(i+j+1)
					except:
						pass  # Ignore events that are already grouped like Festivals
				
				
		if stagedata == 'x':
			stagedata = self.finalStages
		if saledata == 'x':
			saledata = self.sales

		stagedata.sort(key=itemgetter('dates'))
		saledata.sort(key=itemgetter('dates'))
		groupBaronsAndOtherStuff(stagedata)
		dupeCheck(stagedata)
		dupeCheck(saledata)

		
		print('```Events:')
		for group in stagedata:
			print (StageParsers.fancyDate(group['dates'])+group['name'])
		print('```')

		print('```Sales:')
		for group in saledata:
			print (StageParsers.fancyDate(group['dates'])+group['name'])
		print('```')

class ItemFetcher(UniversalFetcher):
	def __init__(self,v='en',f=['M'],d0 = datetime.datetime.today()):
		UniversalFetcher.__init__(self,v,f)
		self.rawData = []
		self.refinedData = []
		self.refinedStages = []
		self.finalStages = []
		self.refinedItems = []
		self.sales = []
		self.date0 = d0

	def fetchRawData(self):		
		if (datetime.datetime.today() - self.date0).days > 60:
			self.fetchLocalData(self.date0)
			return
		url = 'https://bc-seek.godfat.org/seek/%s/item.tsv'%(self.ver)
		response = urllib.request.urlopen(url)
		lines = [l.decode('utf-8') for l in response.readlines()]
		cr = csv.reader(lines, delimiter="\t")
		for row in cr:
			if len(row) > 1:
				self.rawData.append(row)
				row[1],row[3] = (row[1]+'000')[0:3],(row[3]+'000')[0:3]

	def fetchLocalData(self,date):
		d0 = int(date.strftime('%Y%m%d')+'000000')
		mypath = 'Archive\\en\\item\\'
		arr = os.listdir(mypath)
		fname = 0
		for file in arr:
			f = int(file.replace('.tsv',''))
			if f - d0 > 0:
				break
			fname = f
			
		with open(mypath+str(fname)+'.tsv','r', encoding='utf-8') as response:
			lines = response.readlines()
		cr = csv.reader(lines, delimiter="\t")
		for row in cr:
			if len(row) > 1:
				self.rawData.append(row)
				if len(row) > 1 and row[1] == "0":
					row[1] = "0000"
				if len(row) > 3 and row[3] == "0":
					row[3] = "0000"

	def readRawData(self):
		for data in self.rawData:
			if not ItemParsers.areValidDates(ItemParsers.getdates(data),self.filters,self.date0):
				continue
			if data[7] == '0':
				dic = {
					'dates': ItemParsers.getdates(data),
					'versions': ItemParsers.getversions(data),
					'IDs': [data[9]],
					'qty': data[10],
					'text':data[11],
					'recurring': int('0'+data[15])
				}
				
				self.refinedData.append(dic)
				self.refinedStages.append(dic)
			for ID in dic['IDs']:
				if 900 <= int(ID) <= 999:  # Login Stamp
					name = dic['text']+' (Login Stamp)'
				else:
					name = ItemParsers.getItem(GatyaParsers.severToItem(ID))
					if name == 'Unknown':
						continue
				x = dic.copy()
				x['name'] = name
				self.refinedItems.append(x)

	def getStageData(self):
		return (self.finalStages,self.sales)
	
	def printItemData(self):
		print('```Items:')
		for pt,item in enumerate(self.refinedItems):
			if item['name'] in ['Leadership','Rare Ticket'] and item['dates'][0].day == 22 and item['dates'][1].day == 22:
				for ps, i in enumerate(self.refinedItems[pt+1:]):
					if i['name'] in ['Leadership','Rare Ticket'] and item['dates'][0].day == 22 and item['dates'][1].day == 22 and item['name'] != i['name']:
						self.refinedItems.pop(ps+pt+1)
						self.refinedItems[pt]['name'] += f' + {i["name"]} (Meow Meow Day)'
						break
			elif item['name'] == 'Rare Ticket':
				v = item['versions'][0][0:2] +'.'+ str(int(item['versions'][0][2:4]))
				if v in item['text']:
					self.refinedItems[pt]['name'] += f' (for {v} Update)'

		for item in self.refinedItems:
			qty = (' x '+item['qty']) if int(item['qty']) > 1 else ''
			if item['name'] in ['Cat Food','Rare Ticket']  and (item['dates'][1]-item['dates'][0]).days >= 2:
				qty += ' (Daily)' if item['recurring'] else ' (Only Once)'
			print(ItemParsers.fancyDate(item['dates'])+item['name']+qty)
		print('```')
