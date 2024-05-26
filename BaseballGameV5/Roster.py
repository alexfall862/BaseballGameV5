import json
from Player import Player as p 
import os 

class Roster():
    def __init__(self, teamname):
        self.playerlist = Roster.LoadRoster(teamname)

    def LoadRoster(teamname):
        directory = f'..\\Rosters'
        keyword = '_'+teamname+'_'
        for fname in os.listdir(directory):
            if keyword in fname:
                #print(fname, "has the keyword")
                return Roster.Load(directory+f"\\"+fname)
                 

    def Load(directoryjson):
        with open(str(directoryjson)) as f:
            data=json.load(f)
            
        roster = []
        for player in data:
            roster.append(
                p (
                        player['id'],
                        player['ptype'],
                        player['firstname'],
                        player['lastname'],
                        player['handedness'],
                        player['arm angle'],
                        player['injury risk'],
                        player['durability'],
                        
                        player['contact'],
                        player['power'],
                        player['discipline'],
                        player['eye'],
                        
                        player['basereaction'],
                        player['baserunning'],
                        player['speed'],
                        
                        player['throwpower'],
                        player['throwacc'],
                        player['fieldcatch'],
                        player['fieldreact'],
                        player['fieldspot'],
                        
                        player['catchframe'],
                        player['catchsequence'],

                        player['pendurance'],
                        player['pthrowpower'],
                        player['pgencontrol'],
                        player['pickoff'],
                        player['psequencing'],
                        p.CreatePitch(player['pitch1']['name'], player['pitch1']['ovr'], player['pitch1']['pacc'], player['pitch1']['pcntrl'], player['pitch1']['pbrk'], player['pitch1']['consist']),
                        p.CreatePitch(player['pitch2']['name'], player['pitch2']['ovr'], player['pitch2']['pacc'], player['pitch2']['pcntrl'], player['pitch2']['pbrk'], player['pitch2']['consist']),
                        p.CreatePitch(player['pitch3']['name'], player['pitch3']['ovr'], player['pitch3']['pacc'], player['pitch3']['pcntrl'], player['pitch3']['pbrk'], player['pitch3']['consist']),
                        p.CreatePitch(player['pitch4']['name'], player['pitch4']['ovr'], player['pitch4']['pacc'], player['pitch4']['pcntrl'], player['pitch4']['pbrk'], player['pitch4']['consist']),
                        p.CreatePitch(player['pitch5']['name'], player['pitch5']['ovr'], player['pitch5']['pacc'], player['pitch5']['pcntrl'], player['pitch5']['pbrk'], player['pitch5']['consist']),
                        
                        player['team'],
                        player['level'],
                        
                        player['sp_rating'],
                        player['rp_rating'],
                        player['c_rating'],
                        player['fb_rating'],
                        player['sb_rating'],
                        player['tb_rating'],
                        player['ss_rating'],
                        player['lf_rating'],
                        player['cf_rating'],
                        player['rf_rating'],
                        player['dh_rating'],
                        
                        player['battingorder'],
                        player['pitchingorder'],
                        player['lineup'],
                        
                        player['injurystate'],
                        player['energy']
                    )
               )

        return roster     

    def savejson(directoryjson, listofplayers):
        filestring = str(directoryjson+"lineup"+".json")
        output = [obj.to_dict() for obj in listofplayers]
        jsonoutput = json.dumps(output)
        with open(filestring, "w") as file:
            file.write(jsonoutput)