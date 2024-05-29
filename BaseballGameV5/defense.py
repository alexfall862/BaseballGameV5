weights = {
    "barrel": [ .57, .28, .10, .05, .00, .00, .00, .00, .00],
    "solid":  [ .10, .20, .25, .20, .15, .10, .00, .00, .00],
    "flare":  [ .00, .00, .25, .35, .25, .10, .05, .00, .00],
    "burner": [ .00, .00, .00, .00, .20, .60, .20, .00, .00],
    "under":  [ .00, .00, .00, .05, .15, .25, .35, .15, .05],
    "topped": [ .00, .00, .00, .00, .00, .20, .40, .30, .10],
    "weak":   [ .00, .00, .00, .00, .00, .00, .30, .40, .30]
    }

outcomes = [
    'deep_of',
    'middle_of',
    'shallow_of',
    'deep_if',
    'middle_if',
    'shallow_if',
    'mound',
    'catcher'
    ]

defensivealignment = {
    "far left": {
        'deep_of': ['leftfield'], 
        'middle_of': ['leftfield'], 
        'shallow_of':['leftfield'], 
        'deep_if':['thirdbase'], 
        'middle_if':['thirdbase'], 
        'shallow_if':['thirdbase'], 
        'mound': ['thirdbase', 'pitcher'], 
        'catcher': ['catcher']
        },
    "left": {
        'deep_of': ['leftfield'], 
        'middle_of': ['leftfield'], 
        'shallow_of':['leftfield'], 
        'deep_if':['leftfield'], 
        'middle_if':['leftfield'], 
        'shallow_if':['shortstop', 'thirdbase'], 
        'mound': ['thirdbase', 'shortstop', 'pitcher'], 
        'catcher': ['catcher']
        },
    "center left": {
        'deep_of': ['centerfield', 'leftfield'], 
        'middle_of': ['centerfield', 'leftfield'], 
        'shallow_of':['centerfield', 'leftfield'], 
        'deep_if':['shortstop'], 
        'middle_if':['shortstop'], 
        'shallow_if':['shortstop'], 
        'mound': ['shortstop', 'pitcher'], 
        'catcher': ['catcher']
        },
    "dead center": {
        'deep_of': ['centerfield'], 
        'middle_of': ['centerfield'], 
        'shallow_of':['centerfield'], 
        'deep_if':['center', 'shortstop', 'secondbase'], 
        'middle_if':['shortstop', 'secondbase'], 
        'shallow_if':['shortstop', 'secondbase'], 
        'mound': ['pitcher'], 
        'catcher': ['catcher']
        },
    "center right": {
        'deep_of': ['centerfield', 'rightfield'], 
        'middle_of': ['centerfield', 'rightfield'], 
        'shallow_of':['centerfield', 'rightfield'], 
        'deep_if':['secondbase'], 
        'middle_if':['secondbase'], 
        'shallow_if':['secondbase'], 
        'mound': ['secondbase', 'pitcher'], 
        'catcher': ['catcher']
        },
    "right": {
        'deep_of': ['rightfield'], 
        'middle_of': ['rightfield'], 
        'shallow_of':['rightfield'], 
        'deep_if':['rightfield'], 
        'middle_if':['rightfield'], 
        'shallow_if':['secondase', 'firstbase'], 
        'mound': ['firstbase', 'secondbase', 'pitcher'], 
        'catcher': ['catcher']
        },
    "far right": {
        'deep_of': ['rightfield'], 
        'middle_of': ['rightfield'], 
        'shallow_of':['rightfield'], 
        'deep_if':['firstbase'], 
        'middle_if':['firstbase'], 
        'shallow_if':['firstbase'], 
        'mound': ['firstbase', 'pitcher'], 
        'catcher': ['catcher']
        } 
    }

freehit = [
    ('far left', 'shallow_of'), 
    ('center left', 'shallow_of'), 
    ('center right', 'shallow_of'), 
    ('far right', 'shallow_of'), 
    ('left', 'deep_if'), 
    ('dead center', 'deep_if'), 
    ('right', 'deep_if'), 
    ('left', 'middle_if'), 
    ('dead center', 'middle_if'), 
    ('right', 'middle_if') 
    ]

directlyat = [
    (('left', 'middle_of'), 'leftfield'), 
    (('dead center', 'middle_of'), 'centerfield'), 
    (('right', 'middle_of'), 'rightfield'),
    (('far left', 'middle_if'), 'thirdbase'), 
    (('center left', 'middle_if'), 'shortstop'), 
    (('center right', 'middle_if'), 'secondbase'), 
    (('far right', 'middle_if'), 'firstbase'), 
    (('dead center', 'shallow_if'), 'pitcher'),
    (('dead center', 'mound'), 'pitcher'),
    (('far left', 'catcher'), 'catcher'),
    (('left', 'catcher'), 'catcher'),
    (('center left', 'catcher'), 'catcher'),
    (('dead center', 'catcher'), 'catcher'),
    (('center right', 'catcher'), 'catcher'),
    (('right', 'catcher'), 'catcher'),
    (('far right', 'catcher'), 'catcher')
    ]
class ballmoving():
    def __init__(self, gamestate):
        self.gamestate = gamestate
        print(gamestate.outcome)
        self.specificlocation = None
        self.fieldingdefender = None
        self.fieldingdefenderbackup = None
        self.weights = weights
        self.outcomes = outcomes
        self.defensivealignment = defensivealignment
        self.freehit = freehit
        self.directlyat = directlyat
        
    def SpecificLocationGeneator(self):
        pass

    def DefenderCheck(self):
        pass

    def FieldingCheck(self):
        pass
    
    def GrabFielder(self):
        pass
