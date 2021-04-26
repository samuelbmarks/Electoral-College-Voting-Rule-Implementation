import math
import sys
import random
import csv

'''
All possible preference profiles given A = { Biden (B), Trump (T), Jorgensen (J), Hawkins (H) }

(0) B > T > J > H 		(6) T > B > J > H  		(12) J > B > T > H 		(18) H > B > T > J
(1) B > T > H > J 		(7) T > B > H > J 		(13) J > B > H > T  	(19) H > B > J > T
(2) B > J > T > H 		(8) T > J > B > H  		(14) J > T > B > H 		(20) H > T > B > J
(3) B > J > H > T 		(9) T > J > H > B 		(15) J > T > H > B  	(21) H > T > J > B
(4) B > H > T > J 		(10) T > H > B > J 		(16) J > H > B > T 		(22) H > J > B > T
(5) B > H > J > T  		(11) T > H > J > B 		(17) J > H > T > B 		(23) H > J > T > B

'''
ALL_PROFILES = [('B','T','J','H'),('B','T','H','J'),('B','J','T','H'),('B','J','H','T'),('B','H','T','J'),('B','H','J','T'),
				('T','B','J','H'),('T','B','H','J'),('T','J','B','H'),('T','J','H','B'),('T','H','B','J'),('T','H','J','B'),
				('J','B','T','H'),('J','B','H','T'),('J','T','B','H'),('J','T','H','B'),('J','H','B','T'),('J','H','T','B'),
				('H','B','T','J'),('H','B','J','T'),('H','T','B','J'),('H','T','J','B'),('H','J','B','T'),('H','J','T','B')]
ALT = {}
ALT['B'] = 'Biden'
ALT['T'] = 'Trump'
ALT['J'] = 'Jorgensen'
ALT['H'] = 'Hawkins'

class Voter():
	'''
	A Voter object represents a voting agent.

	voter_id: unique identifier for an agent within its state
	state: the state in which an agent votes in
	preference_profile: array of alternatives that represents an voters preference profile
						(e.g., [alt1, alt2, alt3] translates to alt1 > alt2 > alt3)

	'''
	def __init__(self, voter_id, state):
		self.voter_id = voter_id
		self.state = state
		self.preference_profile = []

	def get_preferences(self):
		return self.preference_profile

class State():
	'''
	A State object represents a state in the United States with electoral votes.

	name: the name of the state (e.g., "New York")
	voters: a list of Voter objects that represent all the voters in the state
	num_voters: number of voters participated in the state
	electoral_votes: number of electoral votes deligated to the state
	alternatives: dictionary of candidates where the candidates symbol is the key and the percentage
					of votes they received in a given state (lambda) is the value

	profile_probabilities: a list to store a profile and the probability of an agent having that profile
	votes: a list to store profiles and the number of votes with that given profile
	points: dictionary where candidates are the key values and the number of points they receive
			the values (used to store points when testing various voting rules)
	'''
	def __init__(self, name, biden, trump, jorgensen, hawkins, num_voters, electoral_votes):
		self.name = name
		self.alternatives = {}
		self.alternatives['B'] = biden
		self.alternatives['T'] = trump
		self.alternatives['J'] = jorgensen
		self.alternatives['H'] = hawkins
		self.num_voters = num_voters
		self.electoral_votes = electoral_votes

		self.voters = []
		self.profile_probabilities = []
		self.votes = []
		self.points = {}

		# Winners:
		self.w_plurality = None
		self.w_borda = None
		self.w_copeland = None
		self.w_twoApproval = None
		self.w_veto = None
		self.w_pluralityRunoff = None
		self.w_stv = None

	def alternativeParameterization(self):
		for profile in ALL_PROFILES:
			alt1 = profile[0]
			alt2 = profile[1]
			alt3 = profile[2]
			alt4 = profile[3]

			probability = ( ( self.alternatives[alt1] / ( self.alternatives[alt1] + self.alternatives[alt2] + self.alternatives[alt3] + self.alternatives[alt4] ) ) *
							( self.alternatives[alt2] / ( self.alternatives[alt2] + self.alternatives[alt3] + self.alternatives[alt4] ) ) *
							( self.alternatives[alt3] / ( self.alternatives[alt3] + self.alternatives[alt4] ) ) )

			self.profile_probabilities.append((profile, probability))

		self.profile_probabilities.sort(key = lambda x: x[1], reverse=True)

	def calculateRankedVotes(self):
		for profile, prob in self.profile_probabilities:
			num = int(prob * self.num_voters)
			self.votes.append((profile,num))

	def printProfileProbabilities(self):
		for profile, prob in self.profile_probabilities:
			print("PROFILE: ",profile[0]," > ",profile[1]," > ",profile[2]," > ",profile[3],": ",prob, sep='')

	def printVotes(self):
		for profile, num_votes in self.votes:
			print("PROFILE: ",profile[0]," > ",profile[1]," > ",profile[2]," > ",profile[3],": ",num_votes, sep='')

	def getWinner(self, rule):
		self.points = dict(sorted(self.points.items(), key=lambda x: x[1], reverse=True))

		# for alt, points in self.points.items():
		# 	print(ALT[alt],'Points:', points)
		# print(ALT[next(iter(self.points))],'wins with',rule)
		
		return next(iter(self.points))

	def setPoints(self):
		self.points['B'] = 0
		self.points['T'] = 0
		self.points['J'] = 0
		self.points['H'] = 0

	def plurality(self):
		'''
		The winner is the candidate with the most first place votes (1-approval). 
		'''
		self.setPoints()

		for profile, num_votes in self.votes:
			alt = profile[0]
			self.points[alt] += num_votes
		
		self.w_plurality = self.getWinner('Plurality')

	def borda(self):
		'''
		The winner is the candidate with the most points where points are assigned to candidates based on their ranking 
		(3 points for first, 2 points for second, 1 point for third, 0 points for fourth).
		'''
		self.setPoints()

		for profile, num_votes in self.votes:
			value = 3
			for alt in profile:
				self.points[alt] += (value * num_votes)
				value -= 1
 
		self.w_borda = self.getWinner('Borda')

	def copeland(self):
		'''
		The winner is the alternative with the highest Copeland score, or the number of pairwise wins (the number of 
		positive outgoing edges in the WMG).
		'''
		self.setPoints()

		# Biden vs Trump
		alt = self.copelandHelper('B','T')
		if alt == 'tie':
			self.points['B'] += 0.5
			self.points['T'] += 0.5
		else:
			self.points[alt] += 1

		# Biden vs Jorgensen
		alt = self.copelandHelper('B','J')
		if alt == 'tie':
			self.points['B'] += 0.5
			self.points['J'] += 0.5
		else:
			self.points[alt] += 1

		# Biden vs Hawkins
		alt = self.copelandHelper('B','H')
		if alt == 'tie':
			self.points['B'] += 0.5
			self.points['H'] += 0.5
		else:
			self.points[alt] += 1

		# Trump vs Jorgensen
		alt = self.copelandHelper('T','J')
		if alt == 'tie':
			self.points['T'] += 0.5
			self.points['J'] += 0.5
		else:
			self.points[alt] += 1

		# Trump vs Hawkins
		alt = self.copelandHelper('T','H')
		if alt == 'tie':
			self.points['T'] += 0.5
			self.points['H'] += 0.5
		else:
			self.points[alt] += 1

		# Jorgensen vs Hawkins
		alt = self.copelandHelper('J','H')
		if alt == 'tie':
			self.points['J'] += 0.5
			self.points['H'] += 0.5
		else:
			self.points[alt] += 1

		self.w_copeland = self.getWinner('Copeland')

	def copelandHelper(self, alt1, alt2):
		'''
		Copeland helper function
		'''
		alt1_votes = 0
		alt2_votes = 0

		for profile, num_votes in self.votes:
			index1 = profile.index(alt1)
			index2 = profile.index(alt2)

			if index1 < index2:
				alt1_votes += num_votes
			else:
				alt2_votes += num_votes

		if alt1_votes > alt2_votes:
			return alt1
		elif alt2_votes > alt2_votes:
			return alt2
		else:
			return 'tie'

	def twoApproval(self):
		'''
		The winner is the candidate with the most first or second place votes.
		'''
		self.setPoints()

		for profile, num_votes in self.votes:
			alt1 = profile[0]
			alt2 = profile[1]
			self.points[alt1] += num_votes
			self.points[alt2] += num_votes
		
		self.w_twoApproval = self.getWinner('2-Approval')

	def veto(self):
		'''
		Winner is the candidate with the least last-place preferences
		'''
		self.setPoints()

		for profile, num_votes in self.votes:
			alt = profile[3]
			self.points[alt] -= num_votes
		
		self.w_veto = self.getWinner('Veto')

	def plurality_runoff(self):
		'''
		The election has two rounds. In the first round, all alternatives except the two with the highest plurality 
		scores drop out. In the second round, the alternative preferred by more voters wins.
		'''
		self.setPoints()

		# First round
		for profile, num_votes in self.votes:
			alt = profile[0]
			self.points[alt] += num_votes

		self.points = dict(sorted(self.points.items(), key=lambda x: x[1]))
		remove = next(iter(self.points))

		self.setPoints()

		# Second round
		for profile, num_votes in self.votes:
			alt = profile[0]
			if alt == remove:
				alt = profile[1]
			self.points[alt] += num_votes

		self.points = dict(sorted(self.points.items(), key=lambda x: x[1], reverse=True))
		# print(ALT[next(iter(self.points))],'wins with Plurality w/ Runoff')
		self.w_pluralityRunoff = next(iter(self.points))

	def stv(self):
		'''
		Single Transferable Vote (STV)
		'''
		self.setPoints()
		removed = []

		# First round
		for profile, num_votes in self.votes:
			alt = profile[0]
			self.points[alt] += num_votes

		scores = dict(sorted(self.points.items(), key=lambda x: x[1]))
		remove = list(scores.keys())[0]
		# print(ALT[remove],'removed after first round')
		removed.append(remove)

		self.setPoints()

		# Second round
		for profile, num_votes in self.votes:
			alt = profile[0]
			i = 1
			while alt in removed:
				alt = profile[i]
				i += 1
			self.points[alt] += num_votes
		
		scores = dict(sorted(self.points.items(), key=lambda x: x[1]))
		remove = list(scores.keys())[1]
		# print(ALT[remove],'removed after second round')
		removed.append(remove)

		self.setPoints()

		# Third round
		for profile, num_votes in self.votes:
			alt = profile[0]
			i = 1
			while alt in removed:
				alt = profile[i]
				i += 1
			self.points[alt] += num_votes

		scores = dict(sorted(self.points.items(), key=lambda x: x[1]))
		remove = list(scores.keys())[2]
		# print(ALT[remove],'removed after third round')
		removed.append(remove)

		winner = set(self.points.keys()) - set(removed)
		# print(ALT[list(winner)[0]],'wins with STV')
		self.w_stv = list(winner)[0]


class Country():

	def __init__(self, states):
		self.states = states
		self.altElectoralVotes = {}
	
	def calcWinner(self, rule):
		self.altElectoralVotes['B'] = 0
		self.altElectoralVotes['T'] = 0
		self.altElectoralVotes['J'] = 0
		self.altElectoralVotes['H'] = 0

		for state in states:
			winner = None
			if rule == 'Plurality':
				winner = state.w_plurality
			elif rule == 'Borda':
				winner = state.w_borda
			elif rule == 'Copeland':
				winner = state.w_copeland
			elif rule == '2-Approval':
				winner = state.w_twoApproval
			elif rule == 'Veto':
				winner = state.w_veto
			elif rule == 'Plurality w/ Runoff':
				winner = state.w_pluralityRunoff
			elif rule == 'STV':
				winner = state.w_stv
				
			self.altElectoralVotes[winner] += state.electoral_votes
			# print(ALT[winner],'wins',state.name,'under',rule,'and receives',state.electoral_votes,'electoral votes')

		self.altElectoralVotes = dict(sorted(self.altElectoralVotes.items(), key=lambda x: x[1], reverse=True))
		for alt in self.altElectoralVotes:
			print(ALT[alt],'Electoral Votes:',self.altElectoralVotes[alt])
		print(ALT[next(iter(self.altElectoralVotes))],'wins with',rule)

if __name__ == "__main__":

	# List to store all states
	states = []

	# Read in data
	with open('2020_election_data.csv') as csvfile:
		readCSV = csv.reader(csvfile, delimiter=',')
		for row in readCSV:
			state = State(row[0],float(row[1]),float(row[2]),float(row[3]),float(row[4]),int(row[5]),int(row[6]))
			state.alternativeParameterization()
			state.calculateRankedVotes()
			state.plurality()
			state.borda()
			state.copeland()
			state.twoApproval()
			state.veto()
			state.plurality_runoff()
			state.stv()
			states.append(state)

	country = Country(states)

	print("PLURALITY SIMULATION")
	country.calcWinner('Plurality')
	print()

	print("BORDA SIMULATION")
	country.calcWinner('Borda')
	print()
	
	print("2-APPROVAL SIMULATION")
	country.calcWinner('2-Approval')
	print()
	
	print("VETO SIMULATION")
	country.calcWinner('Veto')
	print()
	
	print("PLURALITY W/ RUNOFF SIMULATION")
	country.calcWinner('Plurality w/ Runoff')
	print()
	
	print("STV SIMULATION")
	country.calcWinner('STV')
	print()
