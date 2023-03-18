#election_processor.py
#a program for determing the outcome of elections

import csv
from tqdm import tqdm

#function to manage the election process
class Election:
    def __init__(self,election_csv,candidate_csv,votes_csv,vote_below_the_line_csv=False,party_lists_csv=False):
        self.import_election_details(election_csv) #import details about the election
        self.import_candidates(candidate_csv) #import candidate names
        if self.party_list_voting==False:
            self.import_votes(votes_csv) #import raw votes
            self.standardise_votes() #ensure votes are valid integers
            self.validate_votes() #determine if these votes are valid
        elif self.party_list_voting==True: #not fully developed so far
            self.import_votes_party() #import votes using party list voting
            self.standardise_votes_party() #ensure votes are valid integers
            self.validate_votes_party() #determine if these votes are valid
            self.convert_party_votes() #convert party list style votes to candidate style votes
        else:
            print("WARNING : self.party_list_voting is neither true nor false, this should never happen")
            pass #this should never happen
        
        self.convert_votes_to_preference_order() #convert votes from candidate order to preference order for ease of processing
        print('raw votes')
        self.display_raw_votes()
        print('valid votes')
        self.display_valid_votes()
        print('preference votes')
        self.display_preference_order_votes()
        if self.voting_type=='first-past-the-post':
            self.first_past_the_post()
        else:
            self.single_transferable_vote()


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
                    try:
                        self.num_winners = int(extract_data)
                        if self.num_winners<=0:
                            print('there must be a positive number of winners, defaulting to 1')
                            self.num_winners
                        if self.num_winners==1:
                            print('there will be ',self.num_winners,' winner at the election')
                        else:
                            print('there will be ',self.num_winners,' winners at the election')

                        print('There will be ',self.num_winners, 'winners at the election')
                    except ValueError:
                        print('invalid number of winners selected, defaulting to 1')
                        self.num_winners = 1
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
                    try:
                        self.min_candidates = int(extract_data)
                        if self.min_candidates<0: #note 0 is a special case indicating all candidates must be used
                            print("WARNING : Minimum number of candidates must be at least 1, have set minimum to 1")
                            self.max_candidates=1
                    except ValueError:
                        print('WARNING : No minimum number of candidates for validity, defaulting to 1')
                        self.min_candidates = 1
                    if self.min_candidates==0:
                        print("Minimum number of candidates for valid vote : All")
                    else:
                        print("Minimum number of candidates for valid vote : ",self.min_candidates)
                #maximum number of candidates for a valid vote
                elif row_number==6:
                    try:
                        self.max_candidates = int(extract_data)
                        if self.min_candidates<0: #note 0 is a special case indicating all candidates must be used
                            print("WARNING : Maximum number of candidates must be at least 1, have set maximum to 1")
                            self.max_candidates=1
                    except ValueError:
                        print('WARNING : No maximum number of candidates for validity, defaulting to all')
                        self.min_candidates = 0
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
                        self.repeat_candidates_policy = 'discard_from'
                        print('If equal preferences made, matching and lower preferences discarded')
                    elif extract_data=='invalid':
                        self.repeat_candidates_policy = 'invalid'
                        print("If equal preferences made, vote is invalid")
                    elif extract_data=='discard_matching':
                        self.repeat_candidates_policy = 'discard_matching'
                        #note this option will be the same as discard_from unless skipped preferences is allowed with compression
                        print("If equal preferences made, only matching preferences discarded")            
                    else:
                        self.repeat_candidates_policy = 'discard_from'
                        print("WARNING : ",extract_data,' not a valid method of handling matching preferences')
                        print('Defaulting to If equal preferences made, matching and lower preferences discarded') 

                #how to handle missed preferences (I.E numbering 1-6, then putting 8)
                elif row_number==10:
                    if extract_data=='discard_from':
                        self.skip_candidates_policy = 'discard_from'
                        print('Disgard preferences made after a skip')
                    elif extract_data=='invalid':
                        self.skip_candidates_policy = 'invalid'
                        print("A skip makes the whole vote invalid")
                    elif extract_data=='compress':
                        self.skip_candidates_policy = 'compress'
                        #note this option will be the same as discard_from unless skipped preferences is allowed
                        print("A skipped preference will be compressed, I.E 1,2,3,4,6 = 1,2,3,4,5 ")             
                    else:
                        self.too_many_candidates_policy = 'compress'
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
                self.raw_votes.append(row) #add each candidate to the list of candidates
            print('votes imported')

    #import raw votes if there is a party list
    def import_votes_party():
        pass

    #remove non-integer or negative votes
    def standardise_votes(self):
        print('converting votes to valid integers . . .')
        votes = []
        for raw_vote in tqdm(self.raw_votes):
            vote = []
            for raw_choice in raw_vote:
                if raw_choice.isdigit():
                    choice = int(raw_choice) #convert vote to an integer
                    if choice<0:
                        choice = 0 #negative votes are not allowed, default to 0
                else:
                    choice = 0 #default value will be 0, indicating no preference
                #append the processed choice to the vote
                vote.append(choice)
            #append the processed choice to the votes
            votes.append(vote)
            self.raw_votes = votes #these votes are still considered to be raw votes


    def standardise_votes_party(self):
        pass


    #process raw votes into valid votes
    def validate_votes(self):
        print('checking if votes valid . . .')
        #self.min_candidates
        #self.max_candidates
        #self.too_few_candidates_policy
        #self.too_many_candidates_policy
        #self.repeat_candidates_policy
        #self.skip_preferences_policy
        self.num_possible_candidates = len(self.raw_votes[0])
        if self.num_possible_candidates!=self.num_candidates:
            print("WARNING: number of places in votes different to number of candidates in candidate list")
        if self.max_candidates==0:#this means maximum is the total number of candidates
            self.max_candidates = self.num_candidates
        if self.min_candidates==0:#this means the minimum is the total number of candidate
            self.min_candidates = self.num_candidates
        self.valid_votes = []
        invalid_count = 0
        for raw_vote in tqdm(self.raw_votes): #go through all the votes
            vote_valid,vote = self.validate_vote(raw_vote)
            if vote_valid:
                self.valid_votes.append(vote)
            else:
                invalid_count = invalid_count+1
        print(invalid_count, ' votes invalid')
            
    #takes in a vote and determines if it is valid or not (return True/False), as well as the validated vote if True
    def validate_vote(self,input_vote):
        raw_vote = input_vote.copy()
        vote_valid = True #the vote is valid unless it breaks one of our rules
        #first check for skipped preferences, handle options, 'discard from', 'invalid', 'compress'
        last_unskipped_vote = 0
        max_preference = max(raw_vote) #maximum value of preference in vote, should be equal to self.num_possible_candidates
        for i in range(1,max_preference+1): #go through all the legal preference rankings
            #print('i = ',i)
            try:
                #print('not skipped')
                index = raw_vote.index(i) #check if this preference is found
                if last_unskipped_vote == i-1:#if we have not skipped any votes yet
                    #print('no skips yet')
                    last_unskipped_vote = i #record the last unskipped vote
                else: #note for this to occur, self.skip_preferences_policy needs to be compress (otherwise we would have broke out of the loop if a skip occurred)
                    #print('last skip ',last_unskipped_vote)
                    raw_vote[index] = last_unskipped_vote+1 #give it the next value in the order of preferences
                    last_unskipped_vote = last_unskipped_vote+1 #and record this as the last unskipped value
            except ValueError: #if this preference is not found
                #print('skipped ')
                if self.skip_candidates_policy=='invalid':#the whole vote is now invalid
                    vote_valid = False
                    return vote_valid,None #immediately exit, no point handling invalid votes further
                elif self.skip_candidates_policy=='discard_matching':
                    #immediately discard the rest of the preferences (value greater or equal to that skipped)
                    for j,preference in enumerate(raw_vote):
                        if preference>=i:
                            raw_vote[j] = 0 #discarded preferences have a value of zero

                    break #break out of the loop, we will only need to discard from a skip once
                elif self.skip_candidates_policy=='compress':
                    continue #compression is handled under the matching else for "if last_unskipped_vote==i-1"
                else:
                     print("WARNING : Skip candidates policy ",self.skip_candidates_policy, " not valid")

        #now that we have removed or discarded skipped preferences, now we need to handle skipped preferences
        max_preference = max(raw_vote) #maximum value of preference in vote, should be equal to self.num_possible_candidates+1 (to handle for loop)
        i = 1
        while i<=max_preference: #go through all the votes
            num_votes = raw_vote.count(i) #how common is that preference in the list of votes
            if num_votes==1: #this should be the case
                i = i+1
                continue
            elif num_votes==0: #if this is the case, bug in previous step but otherwise ignore
                print("WARNING : SKIPS STILL PRESENT AFTER SKIP REMOVAL STEP")
            else:
                if self.repeat_candidates_policy=='invalid':
                    vote_valid = False
                    return vote_valid,None #immediately exit, no point handling invalid votes further
                elif self.repeat_candidates_policy=='discard_from':
                    #immediately discard the rest of the preferences (value greater or equal to that skipped)
                    for j,preference in enumerate(raw_vote):
                        if preference>=i:
                            raw_vote[j] = 0 #discarded preferences have a value of zero

                    break #no need to continue with processing as all additional preferences are now zero               
                elif self.repeat_candidates_policy=='discard_matching':
                    for j,preference in enumerate(raw_vote):
                        if preference==i:
                            raw_vote[j] = 0 #discard matching preferences
                        elif preference>i:
                            raw_vote[j] = preference-1 #remove the skip in position
                            max_preference = max_preference-1 #max preference is now reduced

                else:
                    print("WARNING : Repeat candidates policy ",self.repeat_candidates_policy, " not valid")
            i = i + 1 #increment i by 1

        #determine the number of candidates where a valid preference was indicated
        num_valid_preferences = 0
        for preference in raw_vote:
            if preference>0:
                num_valid_preferences = num_valid_preferences+1
            else:
                continue
        #determine if the number of candidates indicated is in the allowed range
        #first check it is less than or equal to the maximum
        if num_valid_preferences<=self.max_candidates:#candidates less than the max
            pass #vote is valid
        elif num_valid_preferences>self.max_candidates: #too many candidates indicated 
            if self.too_many_candidates_policy=='invalid': #too many candidates vote invalid
                vote_valid = False
                return vote_valid,None
            elif self.too_many_candidates_policy=='discard_extra': #too many candidates, discard lower ranking preferences
                for j,preference in enumerate(raw_vote):
                    if preference>self.max_candidates:
                        raw_vote[j] = 0 #vote is worth nothing
                #now recalculate the number of valid preferences
                num_valid_preferences = 0
                for preference in raw_vote:
                    if preference>0:
                        num_valid_preferences = num_valid_preferences+1
                    else:
                        continue
            else:
                print("WARNING : ",self.too_many_candidates_policy," not a valid policy")
                print("Defaulting to invalid")
                vote_valid = False
                return vote_valid,None

        else:
            print("WARNING : number of preferences ie neither more than or less/than equal maximum number of candidates, this should never happen")
            #make vote invalid
            vote_valid = False
            return vote_valid,None

        #then that it is more than or equal to the minimum
        if num_valid_preferences>=self.min_candidates: #enough candidates
            pass
        elif num_valid_preferences<self.min_candidates: #not enough candidates
            if self.too_few_candidates_policy=='invalid':
                #make vote invalid
                vote_valid = False
                return vote_valid,None
            else:
                print("WARNING : ",self.too_few_candidates_policy," not a valid policy")
                print("Defaulting to invalid")
                vote_valid = False
                return vote_valid,None
        else:
            print("WARNING : number of preferences ie neither more/equal than or less than the minimum number of candidates, this should never happen")
            #make vote invalid
            vote_valid = False
            return vote_valid,None
                      
        return vote_valid,raw_vote     
            
    #validate party list votes
    def validate_votes_party(self):
        pass

    #convert party list votes into normal candidate based votes
    def convert_party_votes(self):
        pass

    #convert all votes from ballot order to preference order
    def convert_votes_to_preference_order(self):
        self.preference_votes = []
        for vote in tqdm(self.valid_votes): #convert each vote
            preference_vote = self.convert_vote_to_preference_order(vote)
            self.preference_votes.append(preference_vote) #and store the new version


    #convert a vote from ballot order to preference order
    #note preference order uses 0 based indexing
    def convert_vote_to_preference_order(self,vote):
        preference_vote = []
        max_preference = max(vote)
        #note this code relies on all preferences being linear upwards from 1 and unique
        #this is ensured by the validation step
        for i in range(1,max_preference+1): #go through all valid (non-zero) preferences
            preference_index = vote.index(i)#index of the candidate with the ith preference
            preference_vote.append(preference_index)
        return preference_vote


    def display_raw_votes(self):
        for vote in self.raw_votes:
            print(vote)
    
    def display_valid_votes(self):
        for vote in self.valid_votes:
            print(vote)
    
    def display_preference_order_votes(self):
        for vote in self.preference_votes:
            print(vote)

    #run an election using the first past the post (ftp) method
    def first_past_the_post(self):
        num_votes = [0]*self.num_candidates #number of first preference votes (all that matters in ftp) that each candidate has gained
        print("running first past the post election")
        print('counting first preferences')
        for vote in tqdm(self.preference_votes):
            num_votes[vote[0]] = num_votes[vote[0]] + 1 #get the first preference add 1 to the selected candidates vote tally
        #display vote counts
        #first rank the order of vote totals
        ranked_votes,ranked_candidates = self.rank_vote_totals(num_votes)
        #then display the vote totals in descending order
        for i,candidate_id in enumerate(ranked_candidates):
            print(self.candidates[candidate_id][0],' : votes = ',ranked_votes[i]) #print the number of votes of each candidate
        #announce the winner
        if self.num_winners==1:
            print('the winner is')
        else:
            print('the winners are')
        #how many winners left (if less than 0, we have had more ties than we have room for)
        num_winners_determined = 0
        last_total = -1
        #declare who the winners are
        for j,vote_total in enumerate(ranked_votes):
            if vote_total!=last_total: #this candidate did not tie with previous candidate
                if num_winners_determined<self.num_winners: #we still have winners left to announce
                    #announce the winner
                    print(self.candidates[ranked_candidates[j]][0]," : Won! with",vote_total, 'votes')
                    last_total = vote_total
                    num_winners_determined = num_winners_determined + 1 
                else:
                    #there are no more winners left
                    break
            elif vote_total==last_total:
                #there has been a tie
                print(self.candidates[ranked_candidates[j]][0]," : Won! with ",vote_total, ' votes')
                num_winners_determined = num_winners_determined + 1

            else:
                print("WARNING : vote total is neither equal or unequal to last total, this is impossible")
        
        #warn the end user if too many candidates has been elected
        if num_winners_determined>self.num_winners:
            print('due to a tie',num_winners_determined,' candidates elected while there are only ',self.num_winners,' positions. A reelection is needed')

    #run an election using the single transferable vote method
    def single_transferable_vote(self):
        pass #not yet implemented




        
        

    
    #return a list of candidate votes in descending order and a list of candidates by number of votes in descending order
    def rank_vote_totals(self,num_votes):
        copy_num_votes = num_votes.copy() #copy for indexing
        while len(num_votes)>0: #till we have ranked all vote totals
            order_num_votes = [] #number of votes of each candidate in descending order of number of votes
            order_candidates = [] #number of votes
            while (len(num_votes)>0):
                max_votes = max(num_votes) #get the maximum number of votes
                candidate_positions = [i for i in range(self.num_candidates) if copy_num_votes[i]==max_votes] #get the index of places with the most votes
                for position in candidate_positions: #add candidates with this many votes to the ranking
                    order_candidates.append(position) #add the candidates position to the ranked list of candidates
                    order_num_votes.append(max_votes) #add the candidates number of votes to the ranked list of vote totals
                    delete_index = num_votes.index(max_votes) #index in original list to delete so we don't ask for the same maximum twice
                    del num_votes[delete_index] #delete the used element from the list for getting the maximum from
                
        return order_num_votes,order_candidates
        






#main function, run the election
def main():
    election_csv = 'election_csv.csv'
    candidates_csv = 'candidates_csv.csv'
    votes_csv = 'votes_csv.csv'
    election = Election(election_csv,candidates_csv,votes_csv)

if __name__ == "__main__":
    main()