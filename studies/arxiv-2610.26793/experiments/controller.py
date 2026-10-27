"""Provider-neutral SOMA-style log-odds controller."""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

THRESHOLD_GRID=(0.25,0.5,0.75,1.0,1.5,2.0,2.5,3.0,4.0,6.0,8.0,12.0)

def threshold_key(value:float)->str:
    return format(float(value),"g")

def log_odds(probability:float,epsilon:float=1e-6)->float:
    if isinstance(probability,bool) or not isinstance(probability,(int,float)):
        raise ValueError("probability must be numeric")
    if not math.isfinite(float(probability)) or not 0.0<=float(probability)<=1.0:
        raise ValueError("probability must be finite and in [0,1]")
    if not 0.0<epsilon<0.5:
        raise ValueError("epsilon must be between 0 and 0.5")
    p=min(max(float(probability),epsilon),1.0-epsilon)
    return math.log(p/(1.0-p))

@dataclass
class SomaController:
    threshold:float
    reminder_first:bool=True
    intervention_enabled:bool=True
    epsilon:float=1e-6
    score:float=0.0
    reminded:bool=False
    stopped:bool=False

    def __post_init__(self)->None:
        if not math.isfinite(self.threshold) or self.threshold<=0.0:
            raise ValueError("threshold must be positive and finite")
        if not 0.0<self.epsilon<0.5:
            raise ValueError("epsilon must be between 0 and 0.5")

    def observe(self,probability:float)->str:
        if self.stopped:
            return "STOPPED"
        self.score=max(0.0,self.score+log_odds(probability,self.epsilon))
        if self.score==0.0:
            self.reminded=False
            return "CONTINUE"
        if self.reminder_first and not self.reminded:
            self.reminded=True
            self.score=0.0
            return "REMIND"
        if self.intervention_enabled and self.score>=self.threshold:
            self.stopped=True
            return "INTERVENE"
        return "CONTINUE"

def choose_threshold(calibration_cases:Sequence[Mapping[str,Any]],thresholds:Sequence[float]=THRESHOLD_GRID,delta:float=0.0)->tuple[float,dict[str,int]]:
    """Choose the smallest threshold within delta of minimum calibration harm."""
    if not calibration_cases:
        raise ValueError("calibration_cases must not be empty")
    if not math.isfinite(delta) or delta<0.0:
        raise ValueError("delta must be non-negative and finite")
    values=tuple(float(v) for v in thresholds)
    if not values or any(not math.isfinite(v) or v<=0.0 for v in values):
        raise ValueError("thresholds must be positive and finite")
    harms={}
    for value in values:
        key,harm=threshold_key(value),0
        for case in calibration_cases:
            outcomes=case.get("correct_by_threshold")
            if not isinstance(outcomes,Mapping) or key not in outcomes:
                raise ValueError(f"missing outcome for {key}")
            if not isinstance(case.get("baseline_correct"),bool) or not isinstance(outcomes[key],bool):
                raise ValueError("correctness labels must be boolean")
            harm+=int(case["baseline_correct"] and not outcomes[key])
        harms[key]=harm
    minimum=min(harms.values())
    return min(v for v in values if harms[threshold_key(v)]<=minimum+delta),harms

def first_crossing_after_reminder(probabilities:Sequence[float],threshold:float,epsilon:float=1e-6)->int|None:
    """Return the first 1-based threshold crossing in one post-reminder episode."""
    if not math.isfinite(threshold) or threshold<=0.0:
        raise ValueError("threshold must be positive and finite")
    score=0.0
    for index,probability in enumerate(probabilities,start=1):
        score=max(0.0,score+log_odds(probability,epsilon))
        if score==0.0:
            return None
        if score>=threshold:
            return index
    return None
