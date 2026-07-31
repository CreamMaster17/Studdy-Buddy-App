#student improvement measurement. "on track is defined as avg score > lookback attempts meeting assessment passing score"

def is_on_track(assessment, lookback=3):
    
    recent = list(assessment.attempts.all()[:lookback])
    if not recent:
        return None
    avg = sum(a.score for a in recent) / len(recent)
    return avg >= assessment.passing_score