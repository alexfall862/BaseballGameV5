import Stats 

class Player():
    def __init__(self, pid, ptype, firstname, lastname, handedness, armangle, injuryrisk, durability,
                 contact, power, discipline, eye, 
                 basereaction, baserunning, speed, 
                 throwpower, throwacc, fieldcatch, fieldreact, fieldspot, 
                 catchframe, catchsequence, 
                 pendurance, pthrowpower, pgencontrol, pickoff, psequencing, pitch1, pitch2, pitch3, pitch4, pitch5,
                 team, level,
                 sp_rating, rp_rating, c_rating, fb_rating, sb_rating, tb_rating, ss_rating, lf_rating, cf_rating, rf_rating, dh_rating,
                 battingorder, pitchingorder, lineup,
                 injurystate, energy
                 ): 
        
        self.id = pid
        self.ptype = ptype
        self.firstname = firstname
        self.lastname = lastname
        self.name = str(firstname + " " + lastname)

        self.handedness = handedness
        self.armangle = armangle
        self.injuryrisk = injuryrisk
        self.durability = durability

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
        
        self.pendurance = pendurance
        self.pthrowpower = pthrowpower
        self.pgencontrol = pgencontrol
        self.pickoff = pickoff
        self.psequencing = psequencing
        self.pitch1 = pitch1
        self.pitch2 = pitch2
        self.pitch3 = pitch3
        self.pitch4 = pitch4
        self.pitch5 = pitch5
        
        self.team = team
        self.level = level

        self.sp_rating = sp_rating
        self.rp_rating = rp_rating
        self.c_rating = c_rating
        self.fb_rating = fb_rating
        self.sb_rating = sb_rating
        self.tb_rating = tb_rating
        self.ss_rating = ss_rating
        self.lf_rating = lf_rating
        self.cf_rating = cf_rating
        self.rf_rating = rf_rating
        self.dh_rating = dh_rating
        
        self.battingorder = battingorder
        self.pitchingorder = pitchingorder
        self.lineup = lineup

        self.injurystate = injurystate
        self.energy = energy
        
        self.base = None
        self.running = None
        self.out = None
        self.force = None
        
        self.sliding = (((self.baserunning*3) + (self.basereaction)) / 4)

        self.earned_bool = True
        self.on_base_pitcher = None
        # self.pitchcount = 0
        # self.pitchstrikes = 0
        # self.pitchballs = 0        
        # self.earnedruns = 0
        # self.pitch_hbp = 0
        # self.pitch_strikeouts = 0
        # self.pitch_walks = 0
        # self.pickoff_throws = 0

        # self.plateappearances = 0
        # self.singles = 0
        # self.doubles = 0
        # self.triples = 0
        # self.homeruns = 0
        # self.bat_strikeouts = 0
        # self.bat_walks = 0
        # self.bat_hbp = 0

        # self.putouts = 0
        # self.assists = 0
        # self.throwingerrors = 0
        # self.catchingerrors = 0

        # self.currentbase = 0
        # self.stealattempts = 0
        # self.stealsuccess = 0  
        # self.runs = 0

        self.fieldingstats = Stats.FieldingStats(self.id, self.lineup, self.name)
        self.battingstats = Stats.BattingStats(self.id, self.lineup, self.name)
        self.pitchingstats = Stats.PitchingStats(self.id, self.lineup, self.name)
        
    def __repr__(self):
        return f"{self.lineup} {self.name}"# {self.earned_bool} {self.on_base_pitcher}" # f"{self.__dict__}\n"

    def __eq__(self, other):
        if isinstance(other, Player):
            return self.value == other.value
        return False

    def to_dict(self):
        return {
            "id":self.id,
            "ptype":self.ptype,
            "firstname":self.firstname,
            "lastname":self.lastname,
            "handedness":self.handedness,
            "arm angle":self.armangle,
            "injury risk":self.injuryrisk,
            "durability":self.durability,
            "contact": self.contact,
            "power": self.power,
            "discipline": self.discipline,
            "eye": self.eye,
            "basereaction": self.basereaction,
            "baserunning": self.baserunning,
            "speed": self.speed,
            "throwpower": self.throwpower, 
            "throwacc": self.throwacc, 
            "fieldcatch": self.fieldcatch,
            "fieldreact": self.fieldreact, 
            "fieldspot": self.fieldspot, 
            "catchframe": self.catchframe,             
            "catchsequence": self.catchsequence, 
            "pendurance": self.pendurance, 
            "pthrowpower": self.pthrowpower,             
            "pgencontrol": self.pgencontrol, 
            "pickoff": self.pickoff, 
            "psequencing": self.psequencing,
            "pitch1":{
                "name":self.pitch1.name,
                "ovr":self.pitch1.ovr,
                "pacc": self.pitch1.pacc,
                "pcntrl": self.pitch1.pcntrl,
                "pbrk": self.pitch1.pbrk, 
                "consist": self.pitch1.consist,
                },
            "pitch2":{
                "name":self.pitch2.name,
                "ovr":self.pitch2.ovr,
                "pacc": self.pitch2.pacc,
                "pcntrl": self.pitch2.pcntrl,
                "pbrk": self.pitch2.pbrk, 
                "consist": self.pitch2.consist,
                },
            "pitch3":{
                "name":self.pitch3.name,
                "ovr":self.pitch3.ovr,
                "pacc": self.pitch3.pacc,
                "pcntrl": self.pitch3.pcntrl,
                "pbrk": self.pitch3.pbrk, 
                "consist": self.pitch3.consist,
                },
            "pitch4":{
                "name":self.pitch4.name,
                "ovr":self.pitch4.ovr,
                "pacc": self.pitch4.pacc,
                "pcntrl": self.pitch4.pcntrl,
                "pbrk": self.pitch4.pbrk, 
                "consist": self.pitch4.consist,
                },
            "pitch5":{
                "name":self.pitch5.name,
                "ovr":self.pitch5.ovr,
                "pacc": self.pitch5.pacc,
                "pcntrl": self.pitch5.pcntrl,
                "pbrk": self.pitch5.pbrk, 
                "consist": self.pitch5.consist,
                },                
            "team":self.team,
            "level":self.level,
            "sp_rating": self.sp_rating,
            "rp_rating": self.rp_rating,
            "c_rating": self.c_rating,
            "fb_rating": self.fb_rating,
            "sb_rating": self.sb_rating,
            "tb_rating": self.tb_rating,
            "ss_rating": self.ss_rating,
            "lf_rating": self.lf_rating,
            "cf_rating": self.cf_rating,
            "rf_rating": self.rf_rating,
            "dh_rating": self.dh_rating,
            "battingorder": self.battingorder,
            "pitchingorder": self.pitchingorder,            
            "lineup": self.lineup,
            "injurystate": self.injurystate
            }

    class CreatePitch():
        def __init__(self, pitchname, ovr, pacc, pcntrl, pbrk, consist):
            self.name = pitchname
            self.ovr = ovr
            self.pacc = pacc
            self.pcntrl = pcntrl
            self.pbrk = pbrk
            self.consist = consist
        def __repr__(self):
            return f"{self.__dict__}"
    

