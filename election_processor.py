#election_processor.py
#a program for determing the outcome of elections

import csv




#function to manage the election process
class Election:
    def __init__(self,election_csv,candidate_csv,vote_csv,vote_below_the_line_csv=False,party_lists_csv=False):
        self.import_election_details() #import details about the election

    #import basic details about the election 
    def import_election_details(self,election_csv):
        with open(election_csv) as csvfile:
            csv_reader = csv.reader(csvfile,delimiter=',')
            for row in csv_reader:
                print(row)




    #import candidates
    def import_candidates(self,candidate_csv):
        pass

#main function, run the election
def main():
    election_csv = 'election_csv'
    candidates_csv = 'candidates_csv'
    votes_csv = 'votes_csv'
    election = Election(election_csv,candidates_csv,votes_csv)


if __name__ == "__main__":
    main()