
import numpy as np
import pandas as pd
from enum import Enum
from copy import deepcopy

MAX_OUTS = 3
MAX_RUNS_PER_INNING = 5
MAX_INNINGS = 4

class Player: 
    p1b = 1.0
    p2b = 1.0
    p3b = 0.0
    phr = 0.0
    pso = 0.0 #struck out
    pbo = 0.0 #hit but thrown out at first (useful for advancing a player)
    
    def __init__(self, hit_probs):
        self.p1b, self.p2b, self.p3b, self.phr, self.pso, self.pbo = hit_probs
        if ((self.p1b + self.p2b + self.p3b + self.phr + self.pso + self.pbo) != 1.0):
            print("Error with setting player")
            print(hit_probs)
            print((self.p1b + self.p2b + self.p3b + self.phr + self.pso + self.pbo))
        self.hit_probs = [self.p1b, self.p2b, self.p3b, self.phr, self.pso, self.pbo]
    def get_hit(self):
        return np.random.choice(['p1b','p2b','p3b','phr','pso','pbo'], 1,
                           p = self.hit_probs)          
          
class BaseBallAction(Enum):
    Single = 1
    Double = 2
    Triple = 3
    HomeRun = 4
    StrikeOut = 5
    ThrownOut = 6

class BaseballState():
    def __init__(self, inning, runs, outs, base3, base2, base1, inning_start_runs = 0.0, likelihood = 1.0):
        self.inning = inning
        self.runs = runs
        self.inning_start_runs = inning_start_runs
        self.outs = outs
        self.base3 = base3
        self.base2 = base2
        self.base1 = base1
        self.likelihood = likelihood
    def __repr__(self):
         return "Inning: {}, Runs: {}, Inning Start Runs: {}, \n                  Outs: {}, First: {}, Second: {}, Third: {}, \n                  Likelihood: {}".format(self.inning, self.runs, self.inning_start_runs,                                         self.outs, self.base1, self.base2, self.base3, self.likelihood)

    def reset_bases(self):
        self.base1 = 0
        self.base2 = 0
        self.base3 = 0
        
    def increment_inning(self):
        self.inning = self.inning + 1
        self.reset_bases()
        self.outs = 0
        self.inning_start_runs = self.runs
        
    def advance_bases(self, count, new_runner):
        while(count != 0):
            if (self.base3):
                self.runs = self.runs + 1
                self.base3 = self.base2
                self.base2 = self.base1
                self.base1 = new_runner
                #max runs advance inning
                if ((self.runs - self.inning_start_runs)%MAX_RUNS_PER_INNING == 0):
                    self.increment_inning()
                    break
            else:
                self.base3 = self.base2
                self.base2 = self.base1
                self.base1 = new_runner
            new_runner = 0 #only new runner first time through
            count = count - 1
            
    def next_state(self,action, action_probability):
        new_state = deepcopy(self)
        new_state.likelihood = new_state.likelihood*action_probability
        if (action == BaseBallAction.StrikeOut) or (action == BaseBallAction.ThrownOut):
            new_state.outs = new_state.outs + 1
            if (new_state.outs == MAX_OUTS):
                #max outs advance inning
                new_state.increment_inning()
            elif (action == BaseBallAction.ThrownOut): #don't always advance base but will here...also usually throw to first
                new_state.advance_bases(count = 1, new_runner = 0)
        elif (action == BaseBallAction.Single):
            new_state.advance_bases(count = 1, new_runner = 1)
        elif (action == BaseBallAction.Double):
            new_state.advance_bases(count = 2, new_runner = 1)
        elif (action == BaseBallAction.Triple):
            new_state.advance_bases(count = 3, new_runner = 1)
        elif (action == BaseBallAction.HomeRun):
            new_state.advance_bases(count = 4, new_runner = 1)
        return new_state
 
'''
    Runs a multi-hypothesis set of scenarios to determine likelihoods for each final state ate end of game
    This looks like a tree once it is completed where the leaf nodes are the possible final states
'''

def run_player_scenario_mh(all_players, order):
    players = [all_players[i] for i in order]

    runs = [0.0 for i in range(0,MAX_INNINGS*MAX_RUNS_PER_INNING + 1)]
    def run_next_iter(cur_state, player_idx, baseball_action, probability):
        new_state = cur_state.next_state(baseball_action, probability)
        if(new_state.inning > MAX_INNINGS):
            runs[new_state.runs] = runs[new_state.runs] + new_state.likelihood
        else:
            run_next_player(new_state,(player_idx + 1)%len(players)) 


    def run_next_player(cur_state, player_idx):
        current_player = players[player_idx%len(players)]
        if(current_player.p1b > 0.0):
            run_next_iter(cur_state,player_idx,BaseBallAction.Single, current_player.p1b)
        if(current_player.p2b > 0.0):
            run_next_iter(cur_state,player_idx,BaseBallAction.Double, current_player.p2b)
        if(current_player.p3b > 0.0):
            run_next_iter(cur_state,player_idx,BaseBallAction.Triple, current_player.p3b)
        if(current_player.phr > 0.0):
            run_next_iter(cur_state,player_idx,BaseBallAction.HomeRun, current_player.phr)
        if(current_player.pso > 0.0):
            run_next_iter(cur_state,player_idx,BaseBallAction.StrikeOut, current_player.pso)
        if(current_player.pbo > 0.0):
            run_next_iter(cur_state,player_idx,BaseBallAction.ThrownOut, current_player.pbo)    

    start_state = BaseballState(1,0,0,0,0,0)
    state_player_idx = 0    
    run_next_player(start_state, state_player_idx)

    w_sum = 0
    for idx, val in enumerate(runs):
        w_sum = w_sum + val*idx
    #return w_sum
    return MAX_INNINGS*MAX_RUNS_PER_INNING - w_sum

'''
    Runs a a monte-carlo using the players to figure out statistical return
'''

def run_player_scenario_mc_standalone(all_players, order):
    players = [all_players[i] for i in order]

    df = pd.DataFrame(data = [], columns = ['Inning', 'Runs', 'Outs', 'Inning Runs'])
    OUTS = 3
    MAX_RUNS_PER_INNING = 5
    MAX_INNINGS = 4
    MAX_MC_RUNS = 100
    
    for sim_runs in range(0,MAX_MC_RUNS): 
        runs = 0 
        inning = 1 
        current_batter = 0 
        bases = [0,0,0] #b1, b2, b3 
        outs = 0 
        start_runs = 0

        while inning <= MAX_INNINGS:
            batting = True
            result = players[current_batter % len(players)].get_hit()
            current_batter = current_batter + 1
            if (result == 'pbo') or (result == 'pso'):
                outs = outs + 1
                if (outs == 3):
                    #max outs advance inning
                    df.loc[sim_runs*MAX_INNINGS + inning] = (inning, runs, outs, runs - start_runs)
                    inning = inning + 1
                    bases = [0,0,0]
                    outs = 0
                    start_runs = runs
                elif (result == 'pbo'):
                    if (bases[2]):
                        runs = runs + 1
                        bases[2] = bases[1]
                        bases[1] = bases[0]
                        bases[0] = 0
                        #max runs advance inning
                        if ((runs - start_runs)%MAX_RUNS_PER_INNING == 0):
                            df.loc[sim_runs*MAX_INNINGS + inning] = (inning, runs, outs, runs - start_runs)
                            inning = inning + 1
                            bases = [0,0,0]
                            outs = 0
                            start_runs = runs
                    else:
                        bases[2] = bases[1]
                        bases[1] = bases[0]
                        bases[0] = 0
            elif (result == 'p1b'):
                if (bases[2]):
                    runs = runs + 1
                    bases[2] = bases[1]
                    bases[1] = bases[0]
                    bases[0] = 1
                    #max runs advance inning
                    if ((runs - start_runs)%MAX_RUNS_PER_INNING == 0):
                        df.loc[sim_runs*MAX_INNINGS + inning] = (inning, runs, outs, runs - start_runs)
                        inning = inning + 1
                        bases = [0,0,0]
                        outs = 0
                        start_runs = runs
                else:
                    bases[2] = bases[1]
                    bases[1] = bases[0]
                    bases[0] = 1
            elif (result == 'p2b'):
                if (bases[2] or bases[1]):
                    runs = min(runs + bases[2] + bases[1],start_runs + MAX_RUNS_PER_INNING)
                    bases[2] = bases[0]
                    bases[1] = 1
                    bases[0] = 0
                    #max runs advance inning
                    if ((runs - start_runs)%MAX_RUNS_PER_INNING == 0):
                        df.loc[sim_runs*MAX_INNINGS + inning] = (inning, runs, outs, runs - start_runs)
                        inning = inning + 1
                        bases = [0,0,0]
                        outs = 0
                        start_runs = runs
                else:
                    bases[2] = bases[0]
                    bases[1] = 1
                    bases[0] = 0
            elif (result == 'p3b'):
                if (bases[2] or bases[1] or bases[0]):
                    runs = min(runs + bases[2] + bases[1] + bases[0],start_runs + MAX_RUNS_PER_INNING)
                    bases[2] = 1
                    bases[1] = 0
                    bases[0] = 0
                    #max runs advance inning
                    if ((runs - start_runs)%MAX_RUNS_PER_INNING == 0):
                        df.loc[sim_runs*MAX_INNINGS + inning] = (inning, runs, outs, runs - start_runs)
                        inning = inning + 1
                        bases = [0,0,0]
                        outs = 0
                        start_runs = runs
                else:
                    bases[2] = 1
                    bases[1] = 0
                    bases[0] = 0
            elif (result == 'phr'):
                runs = min(runs + bases[2] + bases[1] + bases[0] + 1,start_runs + MAX_RUNS_PER_INNING)
                bases[2] = 0
                bases[1] = 0
                bases[0] = 0
                #max runs advance inning
                if ((runs - start_runs)%MAX_RUNS_PER_INNING == 0):
                    df.loc[sim_runs*MAX_INNINGS + inning] = (inning, runs, outs, runs - start_runs)
                    inning = inning + 1
                    bases = [0,0,0]
                    outs = 0
                    start_runs = runs
    return df
    

#Standalone runner to get a min
def run_player_scenario_mc(all_players, order):
    df = run_player_scenario_mc_standalone(all_players,order)
    average_total_runs = df[df.Inning == MAX_INNINGS]['Runs'].sum()/df[df.Inning == MAX_INNINGS]['Runs'].count()
    #return max runs - average_total since it is a cost not a score
    return MAX_INNINGS*MAX_RUNS_PER_INNING - average_total_runs 

def test():
    players =[Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),          
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),       
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])]
    w_sum_mh = run_player_scenario_mh(players, [0,1,2,3,4,5,6,7,8,9])
    w_sum_mc = run_player_scenario_mc(players, [0,1,2,3,4,5,6,7,8,9])
    print(w_sum_mh,w_sum_mc)
    
    players =[Player([0.5, 0.0, 0.0, 0.0, 0.0, 0.5]),          
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([0.5, 0.0, 0.0, 0.0, 0.0, 0.5]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),       
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([0.5, 0.0, 0.0, 0.0, 0.0, 0.5]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
          Player([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])]
    w_sum_mh = run_player_scenario_mh(players, [0,1,2,3,4,5,6,7,8,9])
    w_sum_mc = run_player_scenario_mc(players, [0,1,2,3,4,5,6,7,8,9])
    print(w_sum_mh,w_sum_mc)
    
    w_sum_mh = run_player_scenario_mh(players, [0,1,2,3,4,5,6,7,8,9])
    w_sum_mc = run_player_scenario_mc(players, [0,1,2,3,4,5,6,7,8,9])
    print(w_sum_mh,w_sum_mc)
    