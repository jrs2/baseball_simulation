# Little league Sabermetrics: baseball_simulation

Trying to figure out the best lineup for my kid's little league team which I coach. I'll be the first to admit they are kids and it doesn't really matter. There are unique rules like 5 runs max per inning that make normal front-loading of lineups non-optimal. I was curious on how to setup there lineup so as to maximize the total number of runs.


## Terminology and Rules

Some of these terms and rules are fairly simplified, e.g. someone could hit a single and the player at first could advance two bases instead of just one. This also doesn't take into account the defense. There may be a specific defense setup. Since a lot of little leagues require you to rotate players in defensive positions, you might try to save good batters until when the best defensive player isn't pitching or playing first base. This simulation doesn't take that into account either 

- Player: This is a batter
- 1b: Single, everyone advances one base
- 2b: Double, everyone advances two bases
- 3b: Triple, everyone advances three bases
- hr: Homerun, everyone scores
- so: Strikeout, no one advances and add one out
- bo: Hit and thrown out, everyone advances one base except batter and add one out
 
    
## Code Setup

There are two Notebooks in this repo and some supporting files. 

The first challenge is a determining the result of a given lineup. A given lineup has a lot of possibilities. We'll limit the probabilities of the six options to where only two of them are filled in, e.g. a player has a 60% chance of single and 40% chance of strikeout. You can run through a single game and get a number or you can run a monte-carlo and get a mean or median. 

What I realized is that for a given starting lineup and starting player within that lineup there are six outcomes with a max of five runs: 0-Runs, 1-Run, 2-Runs, 3-Runs, 4-Runs, or 5-Runs. So each outcome has probability. But it isn't that easy because the last one to bat also effects the start of the next inning. So really for a 10 player team with a max of 5 runs there are 60 possible outcomes. An example is you may have scored 3-Runs but the 4th batter in the lineup is up next, or you could have scored 3-Runs and the 6th batter in the lineup is up next. 

How can we use this to our advantage? Instead of doing a Montecarlo simulation we can do the full permutation, or multi-hypothesis tree for each starting batter in a given lineup. Then instead of having to do monte-carlo, we can compute the tree for the each batter and get the probabilities for the 60 outcomes. Then we can treat this as a Markov chain and use linear algebra to cascade the possibilities. I'm sure there is a method like Singular-Value-Decomposition (SVD) that would solve this but I wanted to use some Genetic algorithms so... 

## Option 1: Genetic Algorithm with Ordered Cross-Over (deap.ipynb)

The lineup can be thought of as a set and this set can be fed through a baseball simulation or the Markove chain to determine median or mean number of runs. The ordered cross-over preserves the set so you don't have batter 1 batting twice. See https://en.wikipedia.org/wiki/Crossover_(genetic_algorithm).
