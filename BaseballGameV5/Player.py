import json

#Need to add Height, Weight, Batting Handedness

class Player():
    def __init__(self, id, ptype, firstname, lastname, fullname, age, 
                 contact, power, discipline, eye, 
                 basereaction, baserunning, speed, 
                 throwpower, throwacc, fieldcatch, fieldreact, fieldspot, 
                 catchframe, catchsequence, 
                 overall, batovr, fieldovr, catchovr, athovr,
                 pendurance, pthrowpower, pgencontrol, pickoff, psequencing, 
                 pitch1ovr, pitch1pacc, pitch1pcntrl, pitch1pbrk, pitch1consist,
                 pitch2ovr, pitch2pacc, pitch2pcntrl, pitch2pbrk, pitch2consist,
                 pitch3ovr, pitch3pacc, pitch3pcntrl, pitch3pbrk, pitch3consist,
                 pitch4ovr, pitch4pacc, pitch4pcntrl, pitch4pbrk, pitch4consist,
                 pitch5ovr, pitch5pacc, pitch5pcntrl, pitch5pbrk, pitch5consist,
                 team, level, displayoverall
                 ): 
        self.id = id
        self.ptype = ptype
        self.firstname = firstname
        self.lastname = lastname
        self.fullname = fullname
        self.age = age
        self.contact = contact
        self.power = power
        self.discipline = discipline
        self.eye = eye
        self.basereaction = basereaction
        self.baserunning = baserunning
        self.speed = speed
        self.throwpower = throwpower
        self.throwacc = throwacc
        self.fieldcatch = fieldcatch
        self.fieldreact = fieldreact
        self.fieldspot = fieldspot
        self.catchframe = catchframe
        self.catchsequence = catchsequence       
        self.overall = overall
        self.batovr = batovr
        self.fieldovr = fieldovr
        self.catchovr = catchovr
        self.athovr = athovr
        self.pendurance = pendurance
        self.pthrowpower = pthrowpower
        self.pgencontrol = pgencontrol
        self.pickoff = pickoff
        self.psequencing = psequencing
        self.pitch1ovr = pitch1ovr
        self.pitch1pacc = pitch1pacc
        self.pitch1pcntrl = pitch1pcntrl
        self.pitch1pbrk = pitch1pbrk
        self.pitch1consist = pitch1consist
        self.pitch2ovr = pitch2ovr
        self.pitch2pacc = pitch2pacc
        self.pitch2pcntrl = pitch2pcntrl
        self.pitch2pbrk = pitch2pbrk
        self.pitch2consist = pitch2consist        
        self.pitch3ovr = pitch3ovr
        self.pitch3pacc = pitch3pacc
        self.pitch3pcntrl = pitch3pcntrl
        self.pitch3pbrk = pitch3pbrk
        self.pitch3consist = pitch3consist
        self.pitch4ovr = pitch4ovr
        self.pitch4pacc = pitch4pacc
        self.pitch4pcntrl = pitch4pcntrl
        self.pitch4pbrk = pitch4pbrk
        self.pitch4consist = pitch4consist
        self.pitch5ovr = pitch5ovr
        self.pitch5pacc = pitch5pacc
        self.pitch5pcntrl = pitch5pcntrl
        self.pitch5pbrk = pitch5pbrk
        self.pitch5consist = pitch5consist
        self.team = team or None
        self.level = level or None
        self.displayoverall = displayoverall or None
    def __repr__(self):
        return f"{self.__dict__}\n"
    

#loadjson
def loadjsonroster(directoryjson):
    roster = []
    
    with open(str(directoryjson + ".json")) as f:
        data=json.load(f)

    for player in data:
        roster.append(
            Player(
                    #don't need all this context info, so can cut that out and just import the direct values - just need to make the class and loader match.
                    player['id'],
                    player['ptype'],
                    player['firstname'],
                    player['lastname'],
                    player['fullname'],
                    player['age'],
                    player['contact']['display'],
                    player['power']['display'],
                    player['discipline']['display'],
                    player['eye']['display'],
                    player['basereaction']['display'],
                    player['baserunning']['display'],
                    player['speed']['display'],
                    player['throwpower']['display'],
                    player['throwacc']['display'],
                    player['fieldcatch']['display'],
                    player['fieldreact']['display'],
                    player['fieldspot']['display'],
                    player['catchframe']['display'],
                    player['catchsequence']['display'],                                   
                    player['overall'],
                    player['batovr'],
                    player['fieldovr'],
                    player['catchovr'],
                    player['athovr'],
                    player['pendurance']['display'],
                    player['pthrowpower']['display'],
                    player['pgencontrol']['display'],
                    player['pickoff']['display'],
                    player['psequencing']['display'],
                    player['pitch1ovr'],
                    player['pitch1']['pacc']['display'], 
                    player['pitch1']['pcntrl']['display'], 
                    player['pitch1']['pbrk']['display'], 
                    player['pitch1']['consist']['display'],
                    player['pitch2ovr'],
                    player['pitch2']['pacc']['display'], 
                    player['pitch2']['pcntrl']['display'], 
                    player['pitch2']['pbrk']['display'], 
                    player['pitch2']['consist']['display'],
                    player['pitch3ovr'],
                    player['pitch3']['pacc']['display'], 
                    player['pitch3']['pcntrl']['display'], 
                    player['pitch3']['pbrk']['display'], 
                    player['pitch3']['consist']['display'],
                    player['pitch4ovr'],
                    player['pitch4']['pacc']['display'], 
                    player['pitch4']['pcntrl']['display'], 
                    player['pitch4']['pbrk']['display'], 
                    player['pitch4']['consist']['display'],
                    player['pitch5ovr'],
                    player['pitch5']['pacc']['display'], 
                    player['pitch5']['pcntrl']['display'], 
                    player['pitch5']['pbrk']['display'], 
                    player['pitch5']['consist']['display'],
                    player['team'],
                    player['level'],
                    player['displayovr'],
                )
           )
    return(roster)