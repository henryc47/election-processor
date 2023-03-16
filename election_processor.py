#election_processor.py
#a program for determing the outcome of elections

import csv
from tqdm import tqdm



"""
#this class represents votes as a list of preferences in candidate order
#votes are imported and then validated in this state
class RawVote:
    def __init__(self,list_votes):
        self.list_votes = list_votes #list of preferences in candidate order

class RawPartyVote:
    def __init__(self,list_votes,list_party_votes):
        self.list_votes = list_votes #list of preferences in candidate order
        self.list_party_votes #list of preferences in party order

class Vote:
    def __init__(self,list_votes):
        self.list_votes = list_votes #list of candidates in preference order
"""

#function to manage the election process
class Election:
    def __init__(self,election_csv,candidate_csv,votes_csv,vote_below_the_line_csv=False,party_lists_csv=False):
        self.import_election_details(election_csv) #import details about the election
        self.import_candidates(candidate_csv) #import candidate names
        if self.party_list_voting==False:
            self.import_votes(votes_csv) #import raw votes
            self.validate_votes() #determine if these votes are valid
        elif self.party_list_voting==True: #not fully developed so far
            self.import_votes_party() #import votes using party list voting
            self.validate_votes_party() #determine if these votes are valid
            self.convert_party_votes() #convert party list style votes to candidate style votes
        else:
            print("WARNING : self.party_list_voting is neither true nor false, this should never happen")
            pass #this should never happen
        
        self.convert_votes_to_preference_order() #convert votes from candidate order to preference order for ease of processing

    #import basic details about the election
    #we still need to add party list options
    def import_election_details(self,election_csv):
        with open(election_csv) as csvfile:
            csv_reader = csv.reader(csvfile,delimiter=',')
            row_number = 0
            for row in csv_reader:
                row_number = row_number + 1
                extract_data = row[1]
                #first row is the type of election
                if row_number==1: 
                    #valid options are first past the post (default) and single transferable vote
                    if extract_data=='first-past-the-post' or extract_data=='fptp':
                        #in first past the post voting, preferences don't matter, those with the most first preferences win
                        self.voting_type = 'first-past-the-post'
                        print('You have selected ',self.voting_type,' election') 
                    elif extract_data=='single-transferable-vote' or extract_data=='stv':
                        self.voting_type = 'single-transferable-vote'
                        print('You have selected ',self.voting_type,' election') 
                        print('WARNING: single transferable vote still in development')
                    else:
                        self.voting_type = 'first-past-the-post'
                        print('WARNING: ',extract_data,' elections not a valid option')
                        print('Defaulting too : ',self.voting_type)
                
                #second row is whether party list voting is enabled
                elif row_number==2:
                    #valid options are no (default) and yes
                    if extract_data=='yes':
                        self.party_list_voting = True
                        print('Party list voting enabled')
                        print('WARNING: party list voting not fully developed')
                    else:
                        self.party_list_voting = False
                        print('party list voting disabled')
                
                #how many winners will there be at the election
                elif row_number==3:
                    self.num_winners = extract_data
                    print('There will be ',extract_data, 'winners at the election')
                #how will non-final ties be eliminated
                elif row_number==4:
                    if extract_data=='same_time':
                        print('Losing candidates will be eliminated at the same time')
                        self.early_tie_handling = 'same_time'
                    else:
                        print('WARNING: ',extract_data,' is not a known method of tie resolution')
                        print("Defaulting to same time handling")
                        print('Losing candidates will be eliminated at the same time')
                        self.early_tie_handling = 'same_time'
                #minimum number of candidates for a valid vote
                elif row_number==5:
                    self.min_candidates = extract_data
                    if self.min_candidates==0:
                        print("Minimum number of candidates for valid vote : All")
                    else:
                        print("Minimum number of candidates for valid vote : ",self.min_candidates)
                #maximum number of candidates for a valid vote
                elif row_number==6:
                    self.max_candidates = extract_data
                    if self.max_candidates==0:
                        print("Maximum number of candidates for valid vote : All")
                    else:
                        print("Maximum number of candidates for valid vote : ",self.max_candidates)
                #how to handle votes where too many candidates named
                elif row_number==7:
                    if extract_data=='discard_extra':
                        self.too_many_candidates_policy = 'discard_extra'
                        print('Extra preferences will be discarded')
                    elif extract_data=='invalid':
                        self.too_many_candidates_policy = 'invalid'
                        print("If too few preferences made, vote is invalid")
                    else:
                        self.too_many_candidates_policy = 'discard_extra'
                        print("WARNING : ",extract_data,' not a valid method of handling excess preferences')
                        print('Defaulting to Extra preferences will be discarded')
                #how to handle votes where too few candidates named
                elif row_number==8:
                    if extract_data=='invalid':
                        self.too_few_candidates_policy = 'invalid'
                        print("If too few preferences made, vote is invalid")
                    else:
                        self.too_few_candidates_policy = 'invalid'
                        print("WARNING : ",extract_data,' not a valid method of handling insufficient preferences')
                        print('Defaulting to vote being invalid')
                #how to handle multiple candidates having the same preference
                elif row_number==9:
                    if extract_data=='discard_from':
                        self.repeat_preferences_policy = 'discard_from'
                        print('If equal preferences made, matching and lower preferences discarded')
                    elif extract_data=='invalid':
                        self.repeat_preferences_policy = 'invalid'
                        print("If equal preferences made, vote is invalid")
                    elif extract_data=='discard_matching':
                        self.repeat_preferences_policy = 'discard_matching'
                        #note this option will be the same as discard_from unless skipped preferences is allowed with compression
                        print("If equal preferences made, only matching preferences discarded")            
                    else:
                        self.too_many_candidates_policy = 'discard_extra'
                        print("WARNING : ",extract_data,' not a valid method of handling matching preferences')
                        print('Defaulting to If equal preferences made, matching and lower preferences discarded') 

                #how to handle missed preferences (I.E numbering 1-6, then putting 8)
                elif row_number==10:
                    if extract_data=='discard_from':
                        self.skip_preferences_policy = 'discard_from'
                        print('Disgard preferences made after a skip')
                    elif extract_data=='invalid':
                        self.skip_preferences_policy = 'invalid'
                        print("A skip makes the whole vote invalid")
                    elif extract_data=='compress':
                        self.skip = 'compress'
                        #note this option will be the same as discard_from unless skipped preferences is allowed
                        print("A skipped preference will be compressed, I.E 1,2,3,4,6 = 1,2,3,4,5 ")             
                    else:
                        self.too_many_candidates_policy = 'discard_extra'
                        print("WARNING : ",extract_data,' not a valid method of handling skipped preferences')
                        print('Defaulting to A skipped preference will be compressed, I.E 1,2,3,4,6 = 1,2,3,4,5')

                elif self.party_list_voting:
                    print('WARNING : Party lists not fully developed')

                else:
                    break

    #import candidates
    def import_candidates(self,candidate_csv):
        self.candidates = []
        with open(candidate_csv) as csvfile:
            csv_reader = csv.reader(csvfile,delimiter=',')
            row_number = 0
            for row in csv_reader:
                self.candidates.append(row) #add each candidate to the list of candidates
        
        self.num_candidates = len(self.candidates)

    #import raw votes            
    def import_votes(self,votes_csv):
        self.raw_votes = [] #a list containing all the vote objects
        with open(votes_csv) as csvfile:
            csv_reader = csv.reader(csvfile,delimiter=',')
            print('importing votes . . .')
            for row in tqdm(csv_reader):
                new_vote = RawVote(row)
                self.raw_votes.append(new_vote) #add each candidate to the list of candidates
            print('votes imported')

    #import raw votes if there is a party list
    def import_votes_party():
        pass


    #process raw votes into valid votes
    def validate_votes(self):
        print('checking if votes valid')
        for raw_vote in tqdm(self.raw_votes):
                
            
    
    #validate party list votes
    def validate_votes_party(self):
        pass

    #convert party list votes into normal candidate based votes
    def convert_party_votes(self):
        pass

    def convert_votes_to_preference_order(self):
        pass

    def display_raw_votes(self):
        for vote in self.raw_votes:
            print(vote.list_votes)


#main function, run the election
def main():
    election_csv = 'election_csv.csv'
    candidates_csv = 'candidates_csv.csv'
    votes_csv = 'votes_csv.csv'
    election = Election(election_csv,candidates_csv,votes_csv)

if __name__ == "__main__":
    main()