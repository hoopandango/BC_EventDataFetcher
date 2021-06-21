import nltk as nl
import pandas as pd
from collections import defaultdict

class Catunits:
	_cats = pd.read_csv('LocalData\\auto_units.tsv', sep='\t')
	_customnames = {}

	@classmethod
	def getUnitCode(cls,identifier, errors):
		try:  # was this a string or a int?
			locator = [int(identifier), 0]
		except (ValueError, TypeError):
			locator = cls.closeEnough(identifier, errors)
			if locator == None:
				return "no result"
			if len(locator[0]) > 1:
				return "name not unique"
			locator[0] = locator[0][0]
		return locator

	@classmethod
	def closeEnough(cls,strToCmp, errors):
		strToCmp = strToCmp.lower()
		names = cls._cats.loc[:, 'enname'].to_list()
		names = [str(x).lower() for x in names]
		# edit distance of everything in the tsv
		dss = list(map(lambda x: nl.edit_distance(x, strToCmp), names))

		closest = [i for i, x in enumerate(dss) if x == min(dss)]

		# from dictionary
		distancedict = defaultdict(list)
		for i in cls._customnames:
			distancedict[nl.edit_distance(strToCmp, i.lower())].append(cls._customnames[i])
		customnames = []
		try:
			customnames = min(distancedict.items())
		except ValueError:  # empty custom names
			customnames.append(errors + 1)
		if min(dss) > errors and customnames[0] > errors:  # both were too bad
			return None
		if min(dss) < customnames[0]:  # normal names were better
			return [closest, min(dss), 'original']  # all of the closest and the distance of the closests
		else:  # custom names were better
			return [customnames[1], customnames[0], 'custom']  # the best matches of all custom names
