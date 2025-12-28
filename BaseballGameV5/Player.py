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
                 injurystate, energy, teamname,
                 # Strategy attributes (from endpoint)
                 stealfreq=10.0, pickofffreq=10.0, plate_approach="normal", pitchchoices=None,
                 # Spray chart splits (sum to 1.0)
                 left_split=0.33, center_split=0.34, right_split=0.33
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

        # Strategy attributes
        self.stealfreq = stealfreq
        self.pickofffreq = pickofffreq
        self.plate_approach = plate_approach
        self.pitchchoices = pitchchoices if pitchchoices is not None else []

        # Spray chart splits (sum to 1.0)
        self.left_split = left_split
        self.center_split = center_split
        self.right_split = right_split

        self.base = None
        self.running = None
        self.out = None
        self.force = None
        
        self.sliding = (((self.baserunning*3) + (self.basereaction)) / 4)

        self.earned_bool = True
        self.on_base_pitcher = None
        self.abilitymodifierscore = 1


        self.og_contact = self.contact
        self.og_power = self.power
        self.og_discipline = self.discipline
        self.og_eye = self.eye
        self.og_basereaction = self.basereaction 
        self.og_baserunning = self.baserunning
        self.og_speed = self.speed
        self.og_throwpower = self.throwpower 
        self.og_throwacc = self.throwacc
        self.og_fieldcatch = self.fieldcatch 
        self.og_fieldreact = self.fieldreact  
        self.og_fieldspot = self.fieldspot
        self.og_catchframe = self.catchframe
        self.og_catchsequence = self.catchsequence 
        self.og_pthrowpower = self.pthrowpower 
        self.og_pgencontrol = self.pgencontrol  
        self.og_pickoff = self.pickoff
        self.og_psequencing = self.psequencing
        self.og_pitch1pacc = self.pitch1.pacc
        self.og_pitch1pcntrl = self.pitch1.pcntrl 
        self.og_pitch1pbrk = self.pitch1.pbrk
        self.og_pitch2pacc = self.pitch2.pacc
        self.og_pitch2pcntrl = self.pitch2.pcntrl
        self.og_pitch2pbrk = self.pitch2.pbrk
        self.og_pitch3pacc = self.pitch3.pacc  
        self.og_pitch3pcntrl = self.pitch3.pcntrl 
        self.og_pitch3pbrk = self.pitch3.pbrk
        self.og_pitch4pacc = self.pitch4.pacc
        self.og_pitch4pcntrl = self.pitch4.pcntrl
        self.og_pitch4pbrk = self.pitch4.pbrk
        self.og_pitch5pacc = self.pitch5.pacc
        self.og_pitch5pcntrl = self.pitch5.pcntrl 
        self.og_pitch5pbrk = self.pitch5.pbrk 




        self.teamname = teamname
        self.fieldingstats = Stats.FieldingStats(self.id, self.lineup, self.name, self.teamname)
        self.battingstats = Stats.BattingStats(self.id, self.lineup, self.name, self.teamname)
        self.pitchingstats = Stats.PitchingStats(self.id, self.lineup, self.name, self.teamname)
        
    def __repr__(self):
        return f"{self.lineup} {self.name}"# {self.earned_bool} {self.on_base_pitcher}" # f"{self.__dict__}\n"

    def __eq__(self, other):
        if isinstance(other, Player):
            return self.id == other.id
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

    def AbilityMod(self):
        self.contact = round( self.og_contact * self.abilitymodifierscore, 2)
        self.power = round( self.og_power * self.abilitymodifierscore, 2)
        self.discipline = round( self.og_discipline * self.abilitymodifierscore, 2)
        self.eye = round( self.og_eye * self.abilitymodifierscore, 2)
        self.basereaction = round( self.og_basereaction * self.abilitymodifierscore, 2)
        self.baserunning = round( self.og_baserunning * self.abilitymodifierscore, 2)
        self.speed = round( self.og_speed * self.abilitymodifierscore, 2)
        self.throwpower = round( self.og_throwpower * self.abilitymodifierscore, 2)
        self.throwacc = round( self.og_throwacc * self.abilitymodifierscore, 2)
        self.fieldcatch = round( self.og_fieldcatch * self.abilitymodifierscore, 2)
        self.fieldreact = round( self.og_fieldreact * self.abilitymodifierscore, 2)
        self.fieldspot = round( self.og_fieldspot * self.abilitymodifierscore, 2)
        self.catchframe = round( self.og_catchframe * self.abilitymodifierscore, 2)
        self.catchsequence = round( self.og_catchsequence * self.abilitymodifierscore, 2)
        self.pthrowpower = round( self.og_pthrowpower * self.abilitymodifierscore, 2)
        self.pgencontrol = round( self.og_pgencontrol * self.abilitymodifierscore, 2)
        self.pickoff = round( self.og_pickoff * self.abilitymodifierscore, 2)
        self.psequencing = round( self.og_psequencing * self.abilitymodifierscore, 2)
        self.pitch1.pacc = round( self.og_pitch1pacc * self.abilitymodifierscore, 2)
        self.pitch1.pcntrl = round( self.og_pitch1pcntrl * self.abilitymodifierscore, 2)
        self.pitch1.pbrk = round( self.og_pitch1pbrk * self.abilitymodifierscore, 2)
        self.pitch2.pacc = round( self.og_pitch2pacc * self.abilitymodifierscore, 2)
        self.pitch2.pcntrl = round( self.og_pitch2pcntrl * self.abilitymodifierscore, 2)
        self.pitch2.pbrk = round( self.og_pitch2pbrk * self.abilitymodifierscore, 2)
        self.pitch3.pacc = round( self.og_pitch3pacc * self.abilitymodifierscore, 2)
        self.pitch3.pcntrl = round( self.og_pitch3pcntrl * self.abilitymodifierscore, 2)
        self.pitch3.pbrk = round( self.og_pitch3pbrk * self.abilitymodifierscore, 2)
        self.pitch4.pacc = round( self.og_pitch4pacc * self.abilitymodifierscore, 2)
        self.pitch4.pcntrl = round( self.og_pitch4pcntrl * self.abilitymodifierscore, 2)
        self.pitch4.pbrk = round( self.og_pitch4pbrk * self.abilitymodifierscore, 2)
        self.pitch5.pacc = round( self.og_pitch5pacc * self.abilitymodifierscore, 2)
        self.pitch5.pcntrl = round( self.og_pitch5pcntrl * self.abilitymodifierscore, 2)
        self.pitch5.pbrk = round( self.og_pitch5pbrk * self.abilitymodifierscore, 2)

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
