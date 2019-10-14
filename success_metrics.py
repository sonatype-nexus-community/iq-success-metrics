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
from requests import Session
from requests.auth import HTTPBasicAuth
#---------------------------------
iq_session = Session()
config = {
	"VulDisTime" : 2, "FixManTime" : 2, "FixAutoTime" : 0.3, "WaiManTime" : 7, "WaiAutoTime" : 0.3, "ProductiveHoursDay" : 7, "AvgHourCost" : 100,
	"risk" : ["LOW", "MODERATE", "SEVERE", "CRITICAL"], "category" : ["SECURITY", "LICENSE", "QUALITY", "OTHER"],
	"status" : ["discoveredCounts", "fixedCounts", "waivedCounts", "openCountsAtTimePeriodEnd"],
	"mttr" : ["mttrLowThreat", "mttrModerateThreat", "mttrSevereThreat", "mttrCriticalThreat", "evaluationCount"],
        "statRates": ["FixRate", "WaiveRate", "DealtRate", "FixPercent", "WaiPercent"]
}

def main():
        parser = argparse.ArgumentParser(description='get some Success Metrics')
        parser.add_argument('-a','--auth',   help='', default="admin:admin321", required=False)
        parser.add_argument('-s','--scope',  help='', type=int, default="6", required=False)
        parser.add_argument('-u','--url',    help='', default="http://localhost:8070", required=False)
        parser.add_argument('-i','--appId',  help='', required=False)
        parser.add_argument('-o','--orgId',  help='', required=False)
        parser.add_argument('-p','--pretty', help='', action='store_true', required=False)
        parser.add_argument('-v','--save',   help='', action='store_true', required=False)
        args = vars(parser.parse_args())
        creds = args["auth"].split(":")
        iq_session.auth = HTTPBasicAuth(creds[0], creds[1] )

        #search for applicationId
        appId = searchApps(args["appId"], args["url"])

        #search for organizationId
        orgId = searchOrgs(args["orgId"], args["url"])

        # get success metrics
        data = get_metrics(args["url"], args["scope"], appId,  orgId ) #collects data with or without filters according to appId and orgId

        if data is None: 
                print("No results found.")
                raise SystemExit

        #cnt is used to aggregate totals from the filtered set of applications.
        #reportSummary will return the final results.
        cnt, reportSummary = {}, {"appNames":[], "orgNames":[], "weeks":[], "timePeriodStart" : []}

        # set the weeks range in the report summary for the required scope.
        for ii in range(0, args["scope"]):
                recency = args["scope"]-ii
                reportSummary["timePeriodStart"].append( get_week_start( recency ) ) 
                reportSummary["weeks"].append( get_week_only( recency ) ) 
        
        # set empty range for scope
        for tt in ["appNumberScan", "appOnboard", "weeklyScans"]:
                cnt.update({ tt : zeros(reportSummary["weeks"]) })

        # building aggregated set of fields.
        for tt in config["status"]:
                cnt.update({ tt: {} })
                for rr in config["risk"]:
                        cnt[tt].update({ rr: zeros(reportSummary["weeks"]) })
                cnt[tt].update({ "TOTAL" : zeros(reportSummary["weeks"]) })

        # loop through applications in success metric data.
        for app in data:
                reportSummary['appNames'].append( app["applicationName"] )
                reportSummary['orgNames'].append( app["organizationName"] )
                
                s = get_aggs_list() # zeroed summary template.
                for a in app["aggregations"]:
                        # process the weekly reports for application.
                        process_week(a, s)

                compute_summary(s)
                app.update({"summary": s})

                j = 0
                for w in s["weeks"]:
                        cnt["appOnboard"][w] += 1
                        if s["evaluationCount"]["rng"][j] != 0:
                                cnt["appNumberScan"][w] += 1
                                cnt["weeklyScans"][w] += s["evaluationCount"]["rng"][j] 

                        for tt in config["status"]:
                                for rr in config["risk"]:
                                        cnt[tt][rr][w] += s[tt]["TOTAL"][rr]["rng"][j]
                                cnt[tt]["TOTAL"][w] += s[tt]["TOTAL"]["rng"][j]
                        j += 1

        #convert the dicts to arrays.
        for tt in ["appNumberScan", "appOnboard", "weeklyScans"]:
                reportSummary.update({ tt : list( cnt[tt].values() ) })

        for tt in config["status"]:
                reportSummary.update({ tt: {} })
                for rr in config["risk"]:
                        reportSummary[tt].update({ rr: list( cnt[tt][rr].values() ) })
                reportSummary[tt].update({ "LIST" : list( reportSummary[tt].values() ) })        
                reportSummary[tt].update({ "TOTAL" : list( cnt[tt]["TOTAL"].values() ) })

        #for x in cnt.keys():
                #reportSummary.update({ x: list( cnt[x].values() ) })

        # Final report with summary and data objects.
        report = {"summary": reportSummary, "apps": data}

        if args["pretty"]:
                print( json.dumps(report, indent=4) )

        if args["save"]:
                with open("successmetrics.json",'w') as f:
                        json.dump(report, f)
                        print( "saved to successmetrics.json" )

        else:
                print("Please use -v option to save to json file and/or -p option to display indented output on screen.")
                print("e.g. $> python3 success_metrics.py -v -p")

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
def avg(n): return rnd(sum(n)/len(n))
def rate(n, d): return 0 if d == 0 else (n/d)
def percent(n, d): return rnd(rate(n, d)*100)
def zeros(n): return dict.fromkeys( n, 0)

def ms_days(v): #convert ms to days
	if v is None: return 0
	else: return round( v/86400000)


def get_aggs_list():
	s = {"weeks":[], "fixedRate":[], "waivedRate":[], "dealtRate":[]}
	s.update(zeros(config["statRates"]))
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
	for m in config["mttr"]:
		if m in a:
			v = a[m]
			if m != "evaluationCount": v = ms_days(v)
			s[m]["rng"].append(v)
	
	#looping arrays to pull data from metrics api.
	for t in config["status"]:
		for c in config["category"]:
			T = 0
			for r in config["risk"]:
				if t in a and c in a[t] and r in a[t][c]:
					v = a[t][c][r]
					s[t][c][r]["rng"].append(v)
					T += v
			s[t][c]["TOTAL"]["rng"].append(T)
		# Totals for status including risk levels
		T = 0 
		for r in config["risk"]:
			v = 0
			for c in config["category"]:
				v += s[t][c][r]["rng"][-1]
			s[t]["TOTAL"][r]["rng"].append(v)
			T += v
		s[t]["TOTAL"]["rng"].append(T)

	s["weeks"].append( get_week_date( a["timePeriodStart"]) ) #set week list for images
	s["fixedRate"].append( calc_FixedRate(s, True) )
	s["waivedRate"].append( calc_WaivedRate(s, True) )
	s["dealtRate"].append( calc_DealtRate(s, True) )

def compute_summary(s):
	for m in config["mttr"]:
		s[m]["avg"] = avg(s[m]["rng"])

	for t in config["status"]:
		for c in config["category"]:
			for r in config["risk"]:
				s[t][c][r]["avg"] = avg(s[t][c][r]["rng"])
			s[t][c]["TOTAL"]["avg"] = avg(s[t][c]["TOTAL"]["rng"])

		for r in config["risk"]:
			s[t]["TOTAL"][r]["avg"] = avg(s[t]["TOTAL"][r]["rng"])

		s[t]["TOTAL"]["avg"] = avg(s[t]["TOTAL"]["rng"])

	s["FixRate"] = calc_FixedRate(s, False)
	s["WaiveRate"] = calc_WaivedRate(s, False)
	s["DealtRate"] = calc_DealtRate(s, False)
	s["FixPercent"] = calc_FixPercent(s)
	s["WaiPercent"] = calc_WaiPercent(s)


#------------------------------------------------------------------------------------

if __name__ == "__main__":
	main()
#raise SystemExit

