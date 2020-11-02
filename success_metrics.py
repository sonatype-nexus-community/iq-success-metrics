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
import time
import json
import sys
import argparse
import requests
import os
import io
#---------------------------------
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

iq_session = requests.Session()
config = {
        "VulDisTime" : 2, "FixManTime" : 2, "FixAutoTime" : 0.3, "WaiManTime" : 7, "WaiAutoTime" : 0.3, "ProductiveHoursDay" : 7, "AvgHourCost" : 100,
        "risk" : ["LOW", "MODERATE", "SEVERE", "CRITICAL"], "category" : ["SECURITY", "LICENSE", "QUALITY", "OTHER"],
        "status" : ["discoveredCounts", "fixedCounts", "waivedCounts", "openCountsAtTimePeriodEnd"],
        "mttr" : ["mttrLowThreat", "mttrModerateThreat", "mttrSevereThreat", "mttrCriticalThreat"],
        "statRates": ["FixRate", "WaiveRate", "DealtRate", "FixPercent", "WaiPercent"],
        "rates": ["fixedRate","waivedRate","dealtRate"]
}

#---------------------------------
#
# Print iterations progress
def printProgressBar (
        iteration, 
        total, 
        prefix = 'Progress:', 
        suffix = 'Complete', 
        decimals = 1, 
        length = 50, 
        fill = '█'):

    time.sleep(0.1)
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()

#---------------------------------
def appChecker(iq_url):
    appList = []
    today = datetime.datetime.today()
    today = today.strftime("%Y-%m-%d")
    url = "{}/api/v2/applications".format(iq_url)
    response = iq_session.get(url)
    rawData = response.json()
    #print(rawData)
    for i in range(0,len(rawData["applications"])):
        appList.append(rawData["applications"][i]["id"])
    d = {today : appList}
    
    if not os.path.exists("output/snapshot.json"):
        with open("output/snapshot.json",'w') as f:
            json.dump(d,f)
            snap = d
            print("Creating snapshot.json")

    else:
        with open("output/snapshot.json") as f:
            snap = json.load(f)
            snap.update(d)
            print("Updating snapshot.json")

            with open("output/snapshot.json",'w') as f:
                json.dump(snap, f)

    print( "saved to output/snapshot.json" )

    return snap,len(appList),today
    

#---------------------------------

#---------------------------------
def checkDates(start_date,end_date):
    today = datetime.datetime.today()
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    
    if end_date > today:
        print("\nERROR: Selected reporting end date is in the future. The latest possible reporting end date is today.")
        raise SystemExit

    elif start_date > end_date:
        print("\nERROR: Selected end date is earlier than the start date.")
        raise SystemExit
    


#---------------------------------
def runScript(args,appId,orgId,first,last,today):

                t,segments = 0, 11
                printProgressBar(t,segments)

        #-----------------------------------------------------------------------------------   
                t +=1
                printProgressBar(t,segments)
        #-----------------------------------------------------------------------------------
        
                # get success metrics
                
                if args["scope"]:
                        scope = args["scope"]
                        data = get_metrics(args["url"], scope, appId,  orgId ) #collects data with or without filters according to appId and orgId
                        
                elif args["dateRange"]:
                        scope=get_scope(first,last)
                        data = get_metrics_range(args["url"], first, last, appId,  orgId ) #collects data with or without filters according to appId and orgId
                else:
                        print("No scope or date range has been provided")

                #print(data)
                
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

        #-----------------------------------------------------------------------------------   
                t +=1
                printProgressBar(t,segments)
        #-----------------------------------------------------------------------------------
                
                # set the weeks range in the report summary for the required scope.
                if args["scope"]:
                        #print("scope: ",scope)
                        for recency in range(scope, 0, -1):
                                reportSummary["timePeriodStart"].append( get_week_start( recency ) )
                                reportLic["timePeriodStart"].append( get_week_start( recency ) )
                                reportSec["timePeriodStart"].append( get_week_start( recency ) )
                                reportSummary["weeks"].append( get_week_only( recency ) )
                                #print(reportSummary["weeks"])
                                reportLic["weeks"].append( get_week_only( recency ) )
                                reportSec["weeks"].append( get_week_only( recency ) )
                                
                elif args["dateRange"]:
                        for recency in range(scope, 0, -1):
                                reportSummary["timePeriodStart"].append( get_week_start_range( last, recency ) )
                                reportLic["timePeriodStart"].append( get_week_start_range( last, recency ) )
                                reportSec["timePeriodStart"].append( get_week_start_range( last, recency ) )
                                reportSummary["weeks"].append( get_week_only_range( last, recency ) )
                                #print("reportSummary[weeks]: "+str(reportSummary["weeks"]))
                                reportLic["weeks"].append( get_week_only_range( last, recency ) )
                                reportSec["weeks"].append( get_week_only_range( last, recency ) )

                #print("timeperiodstart: "+str(reportSummary["timePeriodStart"]))
                reportSummary["dates"] = reportSummary["timePeriodStart"]
                reportLic["dates"] = reportLic["timePeriodStart"]
                reportSec["dates"] = reportSec["timePeriodStart"]
                

        #-----------------------------------------------------------------------------------   
                t +=1
                printProgressBar(t,segments)
        #-----------------------------------------------------------------------------------

                
                # building aggregated set of fields for MTTR
                for mttr in config["mttr"]:
                        reportAverages.update({mttr: empties(reportSummary["timePeriodStart"]) })
                        reportAveragesLic.update({mttr: empties(reportLic["timePeriodStart"]) })
                        reportAveragesSec.update({mttr: empties(reportSec["timePeriodStart"]) })
                        

                # set empty range for scope
                for fields in ["appNumberScan", "appOnboard", "weeklyScans","riskRatioCritical","riskRatioSevere","riskRatioModerate","riskRatioLow"]:
                        reportCounts.update({ fields : zeros(reportSummary["timePeriodStart"]) })
                        #print("reportSummary[timeperiodstart]"+str(reportSummary["timePeriodStart"]))
                        #print("reportCounts: "+str(reportCounts))
                        reportCountsLic.update({ fields : zeros(reportLic["timePeriodStart"]) })
                        reportCountsSec.update({ fields : zeros(reportSec["timePeriodStart"]) })

                # building aggregated set of fields.
                for status in config["status"]:
                        reportCounts.update({ status: {} })
                        reportCountsLic.update({ status: {} })
                        reportCountsSec.update({ status: {} })
                        
                        for risk in config["risk"]:
                                reportCounts[status].update({ risk: zeros(reportSummary["timePeriodStart"]) })
                                reportCountsLic[status].update({ risk: zeros(reportLic["timePeriodStart"]) })
                                reportCountsSec[status].update({ risk: zeros(reportSec["timePeriodStart"]) })
                        reportCounts[status].update({ "TOTAL" : zeros(reportSummary["timePeriodStart"]) })
                        reportCountsLic[status].update({ "TOTAL" : zeros(reportLic["timePeriodStart"]) })
                        reportCountsSec[status].update({ "TOTAL" : zeros(reportSec["timePeriodStart"]) })
                
        #-----------------------------------------------------------------------------------   
                t +=1
                printProgressBar(t,segments)
        #-----------------------------------------------------------------------------------


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

                        #print(app_summary["dates"])
                        
                        for date_no in app_summary["dates"]:
                                #print(app_summary["dates"])
                                position = app_summary["dates"].index(date_no)
                                #print("position: "+str(position))
                                if date_no in reportCounts["appOnboard"]:
                                        reportCounts["appOnboard"][date_no] += 1
                                if date_no in reportCountsLic["appOnboard"]:
                                        reportCountsLic["appOnboard"][date_no] += 1
                                if date_no in reportCountsSec["appOnboard"]:
                                        reportCountsSec["appOnboard"][date_no] += 1

                                # only include the app's week when they have a value
                                for mttr in config["mttr"]:
                                        value = app_summary[mttr]["rng"][position]
                                        #print(value)
                                        if value is not None:
                                                #print(reportAverages[mttr][date_no])
                                                if date_no in reportAverages[mttr]:
                                                        reportAverages[mttr][date_no].append( value )
                                                if date_no in reportAveragesLic[mttr]:
                                                        reportAveragesLic[mttr][date_no].append( value )
                                                if date_no in reportAveragesSec[mttr]:
                                                        reportAveragesSec[mttr][date_no].append( value )

                                if app_summary["evaluationCount"]["rng"][position] != 0:
                                        if date_no in reportCounts["appNumberScan"]:
                                                reportCounts["appNumberScan"][date_no] += 1
                                        if date_no in reportCountsLic["appNumberScan"]:
                                                reportCountsLic["appNumberScan"][date_no] += 1
                                        if date_no in reportCountsSec["appNumberScan"]:
                                                reportCountsSec["appNumberScan"][date_no] += 1
                                        if date_no in reportCounts["weeklyScans"]:                                    
                                                reportCounts["weeklyScans"][date_no] += app_summary["evaluationCount"]["rng"][position] 
                                        if date_no in reportCountsLic["weeklyScans"]:
                                                reportCountsLic["weeklyScans"][date_no] += app_summary["evaluationCount"]["rng"][position] 
                                        if date_no in reportCountsSec["weeklyScans"]:
                                                reportCountsSec["weeklyScans"][date_no] += app_summary["evaluationCount"]["rng"][position] 

                                for status in config["status"]:
                                        for risk in config["risk"]:
                                                if date_no in reportCounts[status][risk]:
                                                        reportCounts[status][risk][date_no] += app_summary[status]["TOTAL"][risk]["rng"][position]
                                                if date_no in reportCountsLic[status][risk]:
                                                        reportCountsLic[status][risk][date_no] += app_summary[status]["LICENSE"][risk]["rng"][position]
                                                if date_no in reportCountsSec[status][risk]:
                                                        reportCountsSec[status][risk][date_no] += app_summary[status]["SECURITY"][risk]["rng"][position]
                                        if date_no in reportCounts[status]["TOTAL"]:
                                                reportCounts[status]["TOTAL"][date_no] += app_summary[status]["TOTAL"]["rng"][position]
                                        if date_no in reportCountsLic[status]["TOTAL"]:
                                                reportCountsLic[status]["TOTAL"][date_no] += app_summary[status]["LICENSE"]["TOTAL"]["rng"][position]
                                        if date_no in reportCountsSec[status]["TOTAL"]:
                                                reportCountsSec[status]["TOTAL"][date_no] += app_summary[status]["SECURITY"]["TOTAL"]["rng"][position]

                                #for rates in config["rates"]:
                                #        for risk in config["risk"]:
                                #                reportCounts[rates][risk][date_no] += app_summary[rates]["TOTAL"][risk]["rng"][position]
                                #        reportCounts[rates]["TOTAL"][date_no] += app_summary[rates]["TOTAL"]["rng"][position]

                #-----------------------------------------------------------------------------------

        #-----------------------------------------------------------------------------------   
                t +=1
                printProgressBar(t,segments)
        #-----------------------------------------------------------------------------------


                #convert the dicts to arrays.
                for fields in ["appNumberScan", "appOnboard", "weeklyScans"]:
                        reportSummary.update({ fields : list( reportCounts[fields].values() ) })
                        reportLic.update({ fields : list( reportCountsLic[fields].values() ) })
                        reportSec.update({ fields : list( reportCountsSec[fields].values() ) })

        #-----------------------------------------------------------------------------------   
                t +=1
                printProgressBar(t,segments)
        #-----------------------------------------------------------------------------------


                # calculate the averages for each week.  Returns None when no values are available for a given week. 
                for mttr in config["mttr"]:
                        reportSummary.update({ mttr: list( avg(value) for value in reportAverages[mttr].values()) })
                        reportLic.update({ mttr: list( avg(value) for value in reportAveragesLic[mttr].values()) })
                        reportSec.update({ mttr: list( avg(value) for value in reportAveragesSec[mttr].values()) })

        #-----------------------------------------------------------------------------------   
                t +=1
                printProgressBar(t,segments)
        #-----------------------------------------------------------------------------------

                
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

        #-----------------------------------------------------------------------------------   
                t +=1
                printProgressBar(t,segments)
        #-----------------------------------------------------------------------------------

                for week_no in range(0,len(reportSummary['weeks'])):
                    #print("\n"+str(reportSummary['appOnboard'][week_no]))
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
        #-----------------------------------------------------------------------------------   
                t +=1
                printProgressBar(t,segments)
        #-----------------------------------------------------------------------------------


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
        #-----------------------------------------------------------------------------------   
                t +=1
                printProgressBar(t,segments)
        #-----------------------------------------------------------------------------------


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
                t +=1
                printProgressBar(t,segments)
        #-----------------------------------------------------------------------------------

                #-----------------------------------------------------------------------------------
                # Setting the default to output to json file with the option to format it to human readable.

                ## make an output directory
                os.makedirs("output", exist_ok=True)
                print("Generating "+str(today)+"_successmetrics.json")
                with open("output/"+str(today)+"_successmetrics.json",'w') as f:
                        if args["pretty"]:
                                f.write(json.dumps(report, indent=4))
                        else:
                                json.dump(report, f)
                print( "saved to output/"+str(today)+"_successmetrics.json" )
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

    

#---------------------------------

def main():

        
        parser = argparse.ArgumentParser(description="Sample command: python3 success_metrics.py -a admin:admin123 -s 50 -u 'http://localhost:8070' -i 'd8f63854f4ea4405a9600e34f4d4514e','Test App1','MyApp3' -o 'c6f2775a45d44d43a32621536e638a8e','The A Team' -p -r")
        parser.add_argument('-a','--auth',   help='(in the format user:password, by default admin:admin123)', default="admin:admin123", required=False)
        parser.add_argument('-s','--scope',  help='(number of weeks from current one to gather data from)', type=int, required=False)
        parser.add_argument('-u','--url',    help='(URL for IQ server, by default http://localhost:8070)', default="http://localhost:8070", required=False)
        parser.add_argument('-k','--insecure', help='(Disable SSL Certificate Validation)', action='store_true', required=False)
        parser.add_argument('-i','--appId',  help='(list of application IDs, application Names, application Public IDs or combination thereof to filter from all available data. Default is all available data)', required=False)
        parser.add_argument('-o','--orgId',  help='(list of organization IDs, organization Names or combination thereof to filter from all available data. Default is all available data)', required=False)
        parser.add_argument('-p','--pretty', help='(indents the JSON printout 4 spaces. Default is no indentation)', action='store_true', required=False)
        parser.add_argument('-r','--reports', help='(generates the executive report and the table report for all violations)', action='store_true',required=False)
        parser.add_argument('-rs','--reportsSec', help='(same as -r but only for Security violations)', action='store_true',required=False)
        parser.add_argument('-rl','--reportsLic', help='(same as -r but only for Licensing violations)', action='store_true',required=False)
        parser.add_argument('-d','--dateRange',    help='(creates JSON for a specified date range [yyyy-mm-dd:yyyy-mm-dd]. Do not use in conjunction with -s option)', required=False)
        parser.add_argument('-snap','--snapshot', help='(runs the script just for the apps present in the specified snapshot date)',required=False)
        
        

        args = vars(parser.parse_args())
        creds = args["auth"].split(":",1)
        first, last = [], []
        if args["dateRange"]:
                dateRange = args["dateRange"].split(":",1)
                first = dateRange[0].split("-",2)
                last = dateRange[1].split("-",2)
                start_date = dateRange[0]
                end_date = dateRange[1]
                checkDates(start_date,end_date)

        iq_session.auth = requests.auth.HTTPBasicAuth(str(creds[0]), str(creds[1]) )
        
        if args["insecure"] == True:
            print("WARNING: Ignoring SSL Certificate Validation")
            iq_session.verify = False

        if not os.path.exists("output"):
            os.mkdir("output")

        # checking app number, creating snapshot and storing today's date
        snap,appNumber,today = appChecker(args["url"])

        #search for applicationId
        if args["snapshot"]:
            if not os.path.exists("output/snapshot.json"):
                print("\nERROR: cannot find snapshot.json. Please run the script without -snap option to generate a new snapshot.json")
                raise SystemExit
                
            else:
                with open("output/snapshot.json") as f:
                    snap = json.load(f)

                if args["snapshot"] in snap:
                    #print("Snapshot found in snapshot.json")
                    #-------------------
                    appId = snap[args["snapshot"]]
                    #-------------------
                else:
                    print("\nERROR: the snapshot (date) selected could not be found in snapshot.json\nPlease select an existing snapshot (date). \nAvailable snapshots: ")
                    for key in snap.items():
                        print(key[0])
                    raise SystemExit
                    
        else:
            appId = searchApps(args["appId"], args["url"])

        #search for organizationId
        orgId = searchOrgs(args["orgId"], args["url"])
        
        #print(appList)
        print("Total number of apps with scan reports in IQ server (including onboarded and later deleted apps): "+str(appNumber))

        
#-------------------

        runScript(args,appId,orgId,first,last,today)
                

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
        #print("weekstart: ",period)
        return period

def get_week_start_range(last, recency = 0):
        d = datetime.date(int(last[0]),int(last[1]),int(last[2]))
        d = d - datetime.timedelta(days=d.weekday()+((recency-1)*7) )
        period = '{}'.format( d.isoformat() )
        #print("weekstart: ",period)
        return period


def get_week_only(recency = 0):
        d = datetime.date.today() - datetime.timedelta(days=((recency)*7))
        period = '{}'.format(d.isocalendar()[1])
        #print("weekonly: ",period)
        return period

def get_week_only_range(last,recency = 0):
        d = datetime.date(int(last[0]),int(last[1]),int(last[2])) - datetime.timedelta(days=((recency-1)*7))
        period = '{}'.format(d.isocalendar()[1])
        #print("weekonly: ",period)
        return period

def get_scope(first,last):
 
        from datetime import date

        d1 = date(int(last[0]),int(last[1]),int(last[2]))
        d2 = date(int(first[0]),int(first[1]),int(first[2]))
        aux = (d1-d2).days
        scope = aux//7
        scope += 1
        if aux%7 != 0:
            scope += 1
        return scope
                                                  
def get_week(recency = 0): # recency is number of weeks prior to current week.
        d = datetime.date.today() - datetime.timedelta(days=(recency*7))
        period = '{}-W{}'.format(d.year , d.isocalendar()[1])
        return period

def get_ISO_week(date): # date is needed to calculate ISO week
        d = datetime.date(int(date[0]),int(date[1]),int(date[2]))
        #print(d)
        if d.month == 12 and d.isocalendar()[1] == 1:
            period = '{}-W{}'.format(d.year+1 , d.isocalendar()[1])
        else:
            period = '{}-W{}'.format(d.year , d.isocalendar()[1])    
        #print("ISO week: ",period)
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

def get_metrics_range(iq_url, first, last, appId = [], orgId = []): # first is initial week and last is the last week of the date range.
        url = "{}/api/v2/reports/metrics".format(iq_url)
        iq_header = {'Content-Type':'application/json', 'Accept':'application/json'}
        r_body = {"timePeriod": "WEEK", "firstTimePeriod": get_ISO_week(first) ,"lastTimePeriod": get_ISO_week(last), "applicationIds": appId, "organizationIds": orgId}
        response = iq_session.post( url, json=r_body, headers=iq_header)
        #print(response.json())
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

