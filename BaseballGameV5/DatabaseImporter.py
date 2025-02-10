import mysql.connector
import json

def Connect():
    mydb = mysql.connector.connect(
        host="autorack.proxy.rlwy.net",
        user="root",
        database="railway",
        password="JSbcSPLlEPBuNUGSjIgKXtqyHMJTSFTX",
        port=38564
        )
    return mydb

class Data():
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
   
class InitializeDB():
    def __init__(self):
        self.mydb = Connect()
        self.mycursor = self.mydb.cursor(dictionary=True)

    def pullteam(self, teamID):
        self.mycursor.execute(f"SELECT * FROM organizations AS o JOIN teams AS t on o.mlb = t.teamID WHERE o.org_abbrev ='{teamID}'")
        result = (self.mycursor.fetchall())
        #self.printdata()
        return result

    def printdata(datum):
        listofdata = []
        for data in datum:
            listofdata.append(Data(**data))

        for data in listofdata:
            print(data.__dict__)        