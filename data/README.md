# Description of data files

In this directory are CSV files containing all the data collected from humans and various model baselines. 
The data is organized into two folders corresponding to the two major experiments performed (original_levels and cv_levels)

## Directory structure

Within each directory, the collected human data is under "humans", while the model results are under "models".
Model results consist of 6 ablations/alternatives and the full model:

- ssup_full
  - the full model results
- ablations_phys_mem
  - ablating the prior
- ablations_pri_mem
  - ablating the internal noisy simulation engine
- ablations_pri_phys
  - ablating the update mechanism
- altmod_dqn
  - replacing the prior with a trained deep Q network, and removing the noisy simulation engine
- altmod_param_learn
  - replacing the updating mechanism with inferring the physical parameters of the environment
- guessing_stats
  - random guessing statistics (p(success)). Computed precisely by testing all possible actions.
  
## File structure

### human data
- Each row in the CSV file corresponds to a single action taken by a single participant. 
- The columns correspond to (in order)
  - ID (Participant ID)
  - Trial (one of the level names from the associated experiment)
  - AttemptNum (index of placement number, starting at 0)
  - Tool (name of chosen tool: one of [obj1, obj2, obj3])
  - PosX (X position of placed tool)
  - PosY (Y position of placed tool)
  - Time (time since start of trial, measured in milliseconds)
  - SuccessTrial (True if the participant was eventually successful on this level)
  - TrialOrder (index of trial in experiment for particular individual, starting at 0)
  - SuccessPlace (True if that placement was successful)
  
### model data
- Each row in the CSV file corresponds to a single action taken by a single run of the model
- In every case, the last placement for a given model run was successful unless it took 11 total attempts. If it took 11 attempts, it is classified as unsuccessful.
- The columns correspond to (in order)
  - Trial (one of the level names from the associated experiment)
  - Idx (index of model run, starting at 0. There are 250 runs per model)
  - AttemptNum (index of placement number, starting at 0)
  - TotalAttempts (number of placements made for this level. Maximum 11)
  - Tool (name of chosen tool: one of [obj1, obj2, obj3])
  - PosX (X position of placed tool)
  - PosY (Y position of placed tool)
