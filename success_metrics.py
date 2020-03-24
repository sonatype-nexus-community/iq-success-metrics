#!/usr/bin/python3
# Copyright 2019 Sonatype Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import datetime
import json
import sys
import argparse
import requests
import os
#---------------------------------
iq_session = requests.Session()
config = {
        "VulDisTime" : 2, "FixManTime" : 2, "FixAutoTime" : 0.3, "WaiManTime" : 7, "WaiAutoTime" : 0.3, "ProductiveHoursDay" : 7, "AvgHourCost" : 100,
        "risk" : ["LOW", "MODERATE", "SEVERE", "CRITICAL"], "category" : ["SECURITY", "LICENSE", "QUALITY", "OTHER"],
        "status" : ["discoveredCounts", "fixedCounts", "waivedCounts", "openCountsAtTimePeriodEnd"],
        "mttr" : ["mttrLowThreat", "mttrModerateThreat", "mttrSevereThreat", "mttrCriticalThreat"],
        "statRates": ["FixRate", "WaiveRate", "DealtRate", "FixPercent", "WaiPercent"],
        "rates": ["fixedRate","waivedRate","dealtRate"]
}

def main():
        parser = argparse.ArgumentParser(description='get some Success Metrics')
        parser.add_argument('-a','--auth',   help='', default="admin:admin123", required=False)
        parser.add_argument('-s','--scope',  help='', type=int, default="6", required=False)
        parser.add_argument('-u','--url',    help='', default="http://localhost:8070", required=False)
        parser.add_argument('-i','--appId',  help='', required=False)
        parser.add_argument('-o','--orgId',  help='', required=False)
        parser.add_argument('-p','--pretty', help='', action='store_true', required=False)
        parser.add_argument('-r','--reports', help='', action='store_true',required=False)
        parser.add_argument('-rs','--reportsSec', help='', action='store_true',required=False)
        parser.add_argument('-rl','--reportsLic', help='', action='store_true',required=False)

        args = vars(parser.parse_args())
        creds = args["auth"].split(":")
        iq_session.auth = requests.auth.HTTPBasicAuth(creds[0], creds[1] )
        if not os.path.exists("output"):
            os.mkdir("output")

        #search for applicationId
        appId = searchApps(args["appId"], args["url"])

        #search for organizationId
        orgId = searchOrgs(args["orgId"], args["url"])

        # get success metrics
        data = get_metrics(args["url"], args["scope"], appId,  orgId ) #collects data with or without filters according to appId and orgId

        if data is None: 
                print("No results found.")
                raise SystemExit

        #-----------------------------------------------------------------------------------
        #reportCounts is used to aggregate totals from the filtered set of applications.
        #reportAverages will calculate averages for MTTR. 
        #reportSummary will return the final results.
        #reportLic will return the final results for Licence vulnerabilities only
        #reportSec will return the final results for security vulnerabilities only
        reportAverages, reportCounts, reportSummary = {}, {}, {"appNames":[], "orgNames":[], "weeks":[], "dates":[], "timePeriodStart" : []}
        reportAveragesLic, reportCountsLic, reportLic = {}, {}, {"appNames":[], "orgNames":[], "weeks":[], "dates":[], "timePeriodStart" : []}
        reportAveragesSec, reportCountsSec, reportSec = {}, {}, {"appNames":[], "orgNames":[], "weeks":[], "dates":[], "timePeriodStart" : []}
        
        # set the weeks range in the report summary for the required scope.
        for recency in range(args["scope"], 0, -1):
                reportSummary["timePeriodStart"].append( get_week_start( recency ) )
                reportLic["timePeriodStart"].append( get_week_start( recency ) )
                reportSec["timePeriodStart"].append( get_week_start( recency ) )
                reportSummary["weeks"].append( get_week_only( recency ) )
                reportLic["weeks"].append( get_week_only( recency ) )
                reportSec["weeks"].append( get_week_only( recency ) )
                
        
        # building aggregated set of fields for MTTR
        for mttr in config["mttr"]:
                reportAverages.update({mttr: empties(reportSummary["weeks"]) })
                reportAveragesLic.update({mttr: empties(reportLic["weeks"]) })
                reportAveragesSec.update({mttr: empties(reportSec["weeks"]) })
                

        # set empty range for scope
        for fields in ["appNumberScan", "appOnboard", "weeklyScans","riskRatioCritical","riskRatioSevere","riskRatioModerate","riskRatioLow"]:
                reportCounts.update({ fields : zeros(reportSummary["weeks"]) })
                reportCountsLic.update({ fields : zeros(reportLic["weeks"]) })
                reportCountsSec.update({ fields : zeros(reportSec["weeks"]) })

        # building aggregated set of fields.
        for status in config["status"]:
                reportCounts.update({ status: {} })
                reportCountsLic.update({ status: {} })
                reportCountsSec.update({ status: {} })
                
                for risk in config["risk"]:
                        reportCounts[status].update({ risk: zeros(reportSummary["weeks"]) })
                        reportCountsLic[status].update({ risk: zeros(reportLic["weeks"]) })
                        reportCountsSec[status].update({ risk: zeros(reportSec["weeks"]) })
                reportCounts[status].update({ "TOTAL" : zeros(reportSummary["weeks"]) })
                reportCountsLic[status].update({ "TOTAL" : zeros(reportLic["weeks"]) })
                reportCountsSec[status].update({ "TOTAL" : zeros(reportSec["weeks"]) })

        #-----------------------------------------------------------------------------------
        # loop through applications in success metric data.
        for app in data:
                reportSummary['appNames'].append( app["applicationName"] )
                reportLic['appNames'].append( app["applicationName"] )
                reportSec['appNames'].append( app["applicationName"] )
                reportSummary['orgNames'].append( app["organizationName"] )
                reportLic['orgNames'].append( app["organizationName"] )
                reportSec['orgNames'].append( app["organizationName"] )
                
                app_summary = get_aggs_list() # zeroed summary template.
                for aggregation in app["aggregations"]:
                        # process the weekly reports for application.
                        process_week(aggregation, app_summary)

                compute_summary(app_summary)
                app.update( {"summary": app_summary} )
                app.update( {"licences": app_summary} )
                app.update( {"security": app_summary} )
                

                for week_no in app_summary["weeks"]:
                        position = app_summary["weeks"].index(week_no)
                        reportCounts["appOnboard"][week_no] += 1
                        reportCountsLic["appOnboard"][week_no] += 1
                        reportCountsSec["appOnboard"][week_no] += 1

                        # only include the app's week when they have a value
                        for mttr in config["mttr"]:
                                value = app_summary[mttr]["rng"][position]
                                if not value is None:
                                        reportAverages[mttr][week_no].append( value )
                                        reportAveragesLic[mttr][week_no].append( value )
                                        reportAveragesSec[mttr][week_no].append( value )

                        if app_summary["evaluationCount"]["rng"][position] != 0:
                                reportCounts["appNumberScan"][week_no] += 1
                                reportCountsLic["appNumberScan"][week_no] += 1
                                reportCountsSec["appNumberScan"][week_no] += 1
                                reportCounts["weeklyScans"][week_no] += app_summary["evaluationCount"]["rng"][position] 
                                reportCountsLic["weeklyScans"][week_no] += app_summary["evaluationCount"]["rng"][position] 
                                reportCountsSec["weeklyScans"][week_no] += app_summary["evaluationCount"]["rng"][position] 

                        for status in config["status"]:
                                for risk in config["risk"]:
                                        reportCounts[status][risk][week_no] += app_summary[status]["TOTAL"][risk]["rng"][position]
                                        reportCountsLic[status][risk][week_no] += app_summary[status]["LICENSE"][risk]["rng"][position]
                                        reportCountsSec[status][risk][week_no] += app_summary[status]["SECURITY"][risk]["rng"][position]
                                reportCounts[status]["TOTAL"][week_no] += app_summary[status]["TOTAL"]["rng"][position]
                                reportCountsLic[status]["TOTAL"][week_no] += app_summary[status]["LICENSE"]["TOTAL"]["rng"][position]
                                reportCountsSec[status]["TOTAL"][week_no] += app_summary[status]["SECURITY"]["TOTAL"]["rng"][position]

                        #for rates in config["rates"]:
                        #        for risk in config["risk"]:
                        #                reportCounts[rates][risk][week_no] += app_summary[rates]["TOTAL"][risk]["rng"][position]
                        #        reportCounts[rates]["TOTAL"][week_no] += app_summary[rates]["TOTAL"]["rng"][position]

        #-----------------------------------------------------------------------------------
        #convert the dicts to arrays.
        for fields in ["appNumberScan", "appOnboard", "weeklyScans"]:
                reportSummary.update({ fields : list( reportCounts[fields].values() ) })
                reportLic.update({ fields : list( reportCountsLic[fields].values() ) })
                reportSec.update({ fields : list( reportCountsSec[fields].values() ) })

        # calculate the averages for each week.  Returns None when no values are available for a given week. 
        for mttr in config["mttr"]:
                reportSummary.update({ mttr: list( avg(value) for value in reportAverages[mttr].values()) })
                reportLic.update({ mttr: list( avg(value) for value in reportAveragesLic[mttr].values()) })
                reportSec.update({ mttr: list( avg(value) for value in reportAveragesSec[mttr].values()) })
        
        for status in config["status"]:
                reportSummary.update({ status: {} })
                reportLic.update({ status: {} })
                reportSec.update({ status: {} })

                for risk in config["risk"]:
                        reportSummary[status].update({ risk: list( reportCounts[status][risk].values() ) })
                        reportLic[status].update({ risk: list( reportCountsLic[status][risk].values() ) })
                        reportSec[status].update({ risk: list( reportCountsSec[status][risk].values() ) })
                reportSummary[status].update({ "LIST" : list( reportSummary[status].values() ) })
                reportLic[status].update({ "LIST" : list( reportLic[status].values() ) })
                reportSec[status].update({ "LIST" : list( reportSec[status].values() ) })    
                reportSummary[status].update({ "TOTAL" : list( reportCounts[status]["TOTAL"].values() ) })
                reportLic[status].update({ "TOTAL" : list( reportCountsLic[status]["TOTAL"].values() ) })
                reportSec[status].update({ "TOTAL" : list( reportCountsSec[status]["TOTAL"].values() ) })

        #for rates in config["rates"]:
        #        reportSummary.update({ rates: {} })
        #
        #        for risk in config["risk"]:
        #                reportSummary[rates].update({ risk: list( reportCounts[rates][risk].values() ) })
        #
        #        reportSummary[rates].update({ "LIST" : list( reportSummary[rates].values() ) })        
        #        reportSummary[rates].update({ "TOTAL" : list( reportCounts[rates]["TOTAL"].values() ) })

        riskRatioCri, riskRatioSev, riskRatioMod, riskRatioLow = [],[],[],[]
        for week_no in range(0,len(reportSummary['weeks'])):
                if reportSummary['appOnboard'][week_no] != 0:
                        riskRatioCri.append(str(round((reportSummary['openCountsAtTimePeriodEnd']['CRITICAL'][week_no])/(reportSummary['appOnboard'][week_no]),2)))
                        riskRatioSev.append(str(round((reportSummary['openCountsAtTimePeriodEnd']['SEVERE'][week_no])/(reportSummary['appOnboard'][week_no]),2)))
                        riskRatioMod.append(str(round((reportSummary['openCountsAtTimePeriodEnd']['MODERATE'][week_no])/(reportSummary['appOnboard'][week_no]),2)))
                        riskRatioLow.append(str(round((reportSummary['openCountsAtTimePeriodEnd']['LOW'][week_no])/(reportSummary['appOnboard'][week_no]),2)))
                else:
                        riskRatioCri.append(str(0))
                        riskRatioSev.append(str(0))
                        riskRatioMod.append(str(0))
                        riskRatioLow.append(str(0))
        reportSummary.update({'riskRatioCritical' : riskRatioCri})
        reportSummary.update({'riskRatioSevere' : riskRatioSev})
        reportSummary.update({'riskRatioModerate' : riskRatioMod})
        reportSummary.update({'riskRatioLow' : riskRatioLow})
#-----------------------------------------------------------------------------------------
        riskRatioCri, riskRatioSev, riskRatioMod, riskRatioLow = [],[],[],[]
        for week_no in range(0,len(reportLic['weeks'])):
                if reportLic['appOnboard'][week_no] != 0:
                        riskRatioCri.append(str(round((reportLic['openCountsAtTimePeriodEnd']['CRITICAL'][week_no])/(reportLic['appOnboard'][week_no]),2)))
                        riskRatioSev.append(str(round((reportLic['openCountsAtTimePeriodEnd']['SEVERE'][week_no])/(reportLic['appOnboard'][week_no]),2)))
                        riskRatioMod.append(str(round((reportLic['openCountsAtTimePeriodEnd']['MODERATE'][week_no])/(reportLic['appOnboard'][week_no]),2)))
                        riskRatioLow.append(str(round((reportLic['openCountsAtTimePeriodEnd']['LOW'][week_no])/(reportLic['appOnboard'][week_no]),2)))
                else:
                        riskRatioCri.append(str(0))
                        riskRatioSev.append(str(0))
                        riskRatioMod.append(str(0))
                        riskRatioLow.append(str(0))
        reportLic.update({'riskRatioCritical' : riskRatioCri})
        reportLic.update({'riskRatioSevere' : riskRatioSev})
        reportLic.update({'riskRatioModerate' : riskRatioMod})
        reportLic.update({'riskRatioLow' : riskRatioLow})
#-----------------------------------------------------------------------------------------
        riskRatioCri, riskRatioSev, riskRatioMod, riskRatioLow = [],[],[],[]
        for week_no in range(0,len(reportSec['weeks'])):
                if reportSec['appOnboard'][week_no] != 0:
                        riskRatioCri.append(str(round((reportSec['openCountsAtTimePeriodEnd']['CRITICAL'][week_no])/(reportSec['appOnboard'][week_no]),2)))
                        riskRatioSev.append(str(round((reportSec['openCountsAtTimePeriodEnd']['SEVERE'][week_no])/(reportSec['appOnboard'][week_no]),2)))
                        riskRatioMod.append(str(round((reportSec['openCountsAtTimePeriodEnd']['MODERATE'][week_no])/(reportSec['appOnboard'][week_no]),2)))
                        riskRatioLow.append(str(round((reportSec['openCountsAtTimePeriodEnd']['LOW'][week_no])/(reportSec['appOnboard'][week_no]),2)))
                else:
                        riskRatioCri.append(str(0))
                        riskRatioSev.append(str(0))
                        riskRatioMod.append(str(0))
                        riskRatioLow.append(str(0))
        reportSec.update({'riskRatioCritical' : riskRatioCri})
        reportSec.update({'riskRatioSevere' : riskRatioSev})
        reportSec.update({'riskRatioModerate' : riskRatioMod})
        reportSec.update({'riskRatioLow' : riskRatioLow})
#-----------------------------------------------------------------------------------------
        
        # Final report with summary and data objects.
        report = {"summary": reportSummary, "apps": data, "licences": reportLic, "security": reportSec}

        #-----------------------------------------------------------------------------------
        # Setting the default to output to json file with the option to format it to human readable.

        ## make an output directory
        os.makedirs("output", exist_ok=True)
        print("Generating successmetrics.json")
        with open("output/successmetrics.json",'w') as f:
                if args["pretty"]:
                        f.write(json.dumps(report, indent=4))
                else:
                        json.dump(report, f)
        print( "saved to output/successmetrics.json" )
        #-----------------------------------------------------------------------------------
        # one more thing...
        if args["reports"] == True:
                print("Generating the Executive report")
                os.system('python3 ./reports.py -e')
                print("Generating the Table report")
                os.system('python3 ./reports.py -t')
                
        if args["reportsSec"] == True:
                print("Generating the Executive report just for Security violations")
                os.system('python3 ./reports.py -es')
                print("Generating the Table report just for Security violations")
                os.system('python3 ./reports.py -ts')
                
        if args["reportsLic"] == True:
                print("Generating the Executive report just for Licensing violations")
                os.system('python3 ./reports.py -el')
                print("Generating the Table report just for Licensing violations")
                os.system('python3 ./reports.py -tl')
                
        #-----------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------
def searchApps(search, iq_url):
        appId = []
        if search is not None and len(search) > 0:
                search = search.split(",")
                url = '{}/api/v2/applications'.format(iq_url)
                response = iq_session.get(url).json()
                for app in response["applications"]:
                        for item in search:
                                if item in [app["name"], app["id"], app["publicId"]]:
                                        appId.append(app["id"]) #if app "name", "id" or "publicId" in arguments, then creates array of app IDs in appId
        return appId

def searchOrgs(search, iq_url):
        orgId = []
        if search is not None and len(search) > 0:
                search = search.split(",")               
                url = '{}/api/v2/organizations'.format(iq_url)
                response = iq_session.get(url).json()
                for org in response["organizations"]:
                        for item in search:
                                if item in [org["name"], org["id"]]:
                                        orgId.append(org["id"]) #if org "name", "id" or "publicId" in arguments, then creates array of org IDs in orgId
        return orgId

def get_week_start(recency = 0):
        d = datetime.date.today()
        d = d - datetime.timedelta(days=d.weekday()+(recency*7) )
        period = '{}'.format( d.isoformat() )
        return period

def get_week_only(recency = 0):
        d = datetime.date.today() - datetime.timedelta(days=(recency*7))
        period = '{}'.format(d.isocalendar()[1])
        return period

                                                  
def get_week(recency = 0): # recency is number of weeks prior to current week.
        d = datetime.date.today() - datetime.timedelta(days=(recency*7))
        period = '{}-W{}'.format(d.year , d.isocalendar()[1])
        return period

def get_week_date(s):
        d = datetime.datetime.strptime(s, "%Y-%m-%d")
        period = '{}'.format(d.isocalendar()[1])
        return period

def get_metrics(iq_url, scope = 6, appId = [], orgId = []): # scope is number of week prior to current week.
        url = "{}/api/v2/reports/metrics".format(iq_url)
        iq_header = {'Content-Type':'application/json', 'Accept':'application/json'}
        r_body = {"timePeriod": "WEEK", "firstTimePeriod": get_week(scope) ,"lastTimePeriod": get_week(1), #use get_week(0) instead if looking for Year-To-Date data instead of fully completed weeks
                "applicationIds": appId, "organizationIds": orgId}
        response = iq_session.post( url, json=r_body, headers=iq_header)
        return response.json()

def rnd(n): return round(n,2)
def avg(n): return 0 if len(n) == 0 else rnd(sum(n)/len(n))
def rate(n, d): return 0 if d == 0 else (n/d)
def percent(n, d): return rnd(rate(n, d)*100)
def zeros(n): return dict.fromkeys( n, 0)
def empties(keys): return { key : list([]) for key in keys }

def ms_days(v): #convert ms to days
        if v is None: return 0
        else: return round(v/86400000)


def get_aggs_list():
        s = {"weeks":[], "dates": [], "fixedRate":[], "waivedRate":[], "dealtRate":[]}
        s.update(zeros(config["statRates"]))
        s.update({"evaluationCount":{"rng":[]}})

        for m in config["mttr"]:
                s.update({m:{"avg":0,"rng":[]}})

        for t in config["status"]:
                g = {"TOTAL":{"avg":0,"rng":[]}}
                for c in config["category"]:
                        k = {"TOTAL":{"avg":0,"rng":[]}}
                        for r in config["risk"]:
                                k.update({r:{"avg":0,"rng":[]}})
                        g.update({c:k}) 
                for r in config["risk"]:
                        g["TOTAL"].update({r:{"avg":0,"rng":[]}})
                s.update({t:g})

        #for rates in config["rates"]:
        #        g = {"TOTAL":{"avg":0,"rng":[]}}
        #        for c in config["category"]:
        #                k = {"TOTAL":{"avg":0,"rng":[]}}
        #                for r in config["risk"]:
        #                        k.update({r:{"avg":0,"rng":[]}})
        #                g.update({c:k}) 
        #        for r in config["risk"]:
        #                g["TOTAL"].update({r:{"avg":0,"rng":[]}})
        #        s.update({rates:g})
        return s

#----------------------------------
# Helpers

def get_dCnt(d): return d["discoveredCounts"]["TOTAL"]["rng"]
def get_oCnt(d): return d["openCountsAtTimePeriodEnd"]["TOTAL"]["rng"]
def get_fCnt(d): return d["fixedCounts"]["TOTAL"]["rng"]
def get_wCnt(d): return d["waivedCounts"]["TOTAL"]["rng"]

def calc_FixedRate(d, last=True):
        f, o = get_fCnt(d), get_oCnt(d)
        if last: f, o = f[-1], o[-1]
        else: f, o = sum(f), sum(o)
        return percent(f, o)

def calc_WaivedRate(d, last=True):
        w, o = get_wCnt(d), get_oCnt(d)
        if last: w, o = w[-1], o[-1]
        else: w, o = sum(w), sum(o)
        return percent(w, o)

def calc_DealtRate(d, last=True):
        f, w, o = get_fCnt(d), get_wCnt(d), get_oCnt(d)
        if last: f, w, o = f[-1], w[-1], o[-1]
        else: f, w, o = sum(f), sum(w), sum(o)
        return percent(f+w, o)

def calc_FixPercent(d): 
        f, w = sum(get_fCnt(d)), sum(get_wCnt(d))
        return 0 if (f+w) == 0 else (f/(f+w))

def calc_WaiPercent(d):
        f, w = sum( get_fCnt(d)), sum(get_wCnt(d))
        return 0 if (f+w) == 0 else (w/(f+w))

def calc_DisManCost(d):
        return sum(get_dCnt(d)) * config["AvgHourCost"] * config["VulDisTime"]

def calc_DebtManCost(d):
        return sum(get_oCnt(d)) * config["AvgHourCost"] * ( (calc_FixPercent(d) * config["FixManTime"]) + ( calc_WaiPercent(d) * config["WaiManTime"] ) )

def calc_DebtAutoCost(d):
        return sum(get_oCnt(d)) * config["AvgHourCost"] * ( (calc_FixPercent(d) * config["FixAutoTime"]) + ( calc_WaiPercent(d) * config["WaiAutoTime"] ) )

def calc_TotalSonatypeValue(d):
        return calc_DisManCost(d) + ( calc_DebtManCost(d) - calc_DebtAutoCost(d) )

#------------------------------------------------------------------------------------

def process_week(a, s):
        for mttr in config["mttr"]:
                if mttr in a:
                        value = a[mttr]
                        if not value is None: 
                                value = ms_days(value)
                        s[mttr]["rng"].append(value)
        
        for status in config["status"]:
                for category in config["category"]:
                        Totals = 0
                        for risk in config["risk"]:
                                if status in a and category in a[status] and risk in a[status][category]:
                                        value = a[status][category][risk]
                                        s[status][category][risk]["rng"].append(value)
                                        Totals += value
                        s[status][category]["TOTAL"]["rng"].append(Totals)
                # Totals for status including risk levels
                Totals = 0 
                for risk in config["risk"]:
                        value = 0
                        for category in config["category"]:
                                value += s[status][category][risk]["rng"][-1]
                        s[status]["TOTAL"][risk]["rng"].append(value)
                        Totals += value
                s[status]["TOTAL"]["rng"].append(Totals)

        #INCLUDE fixedRate, waivedRate, dealtRate loop here?

        s["evaluationCount"]["rng"].append( a["evaluationCount"] )
        s["weeks"].append( get_week_date( a["timePeriodStart"]) ) #set week list for images
        s["dates"].append(a["timePeriodStart"]) #set dates list for images
        s["fixedRate"].append( calc_FixedRate(s, True) )
        s["waivedRate"].append( calc_WaivedRate(s, True) )
        s["dealtRate"].append( calc_DealtRate(s, True) )

def compute_summary(s):
        for mttr in config["mttr"]:
                t = []
                for w in s[mttr]["rng"]:
                        if not w is None:
                                t.append(w)
                s[mttr]["avg"] = avg(t)

        for status in config["status"]:
                for category in config["category"]:
                        for risk in config["risk"]:
                                s[status][category][risk]["avg"] = avg(s[status][category][risk]["rng"])
                        s[status][category]["TOTAL"]["avg"] = avg(s[status][category]["TOTAL"]["rng"])

                for risk in config["risk"]:
                        s[status]["TOTAL"][risk]["avg"] = avg(s[status]["TOTAL"][risk]["rng"])

                s[status]["TOTAL"]["avg"] = avg(s[status]["TOTAL"]["rng"])

        #INCLUDE fixedRate, waivedRate, dealtRate loop here?
        s["SonatypeValue"] = calc_TotalSonatypeValue(s)

        s["FixRate"] = calc_FixedRate(s, False)
        s["WaiveRate"] = calc_WaivedRate(s, False)
        s["DealtRate"] = calc_DealtRate(s, False)
        s["FixPercent"] = calc_FixPercent(s)
        s["WaiPercent"] = calc_WaiPercent(s)


#------------------------------------------------------------------------------------

if __name__ == "__main__":
        main()
#raise SystemExit

