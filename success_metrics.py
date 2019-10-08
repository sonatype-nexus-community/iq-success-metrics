#!/usr/bin/python3

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
        #print(data)
        appName, appOnboard, appNumberScan, orgName, weeks = [], [], [], [], []
        disLow, disMod, disSev, disCri, disTotal = [], [], [], [], []
        fixLow, fixMod, fixSev, fixCri, fixTotal = [], [], [], [], []
        waiLow, waiMod, waiSev, waiCri, waiTotal = [], [], [], [], []
        opeLow, opeMod, opeSev, opeCri, opeTotal = [], [], [], [], []
        
        appNumberScandict = dict()
        appOnboarddict = dict()
        disLowdict = dict()
        disModdict = dict()
        disSevdict = dict()
        disCridict = dict()
        disTotaldict = dict()
        fixLowdict = dict()
        fixModdict = dict()
        fixSevdict = dict()
        fixCridict = dict()
        fixTotaldict = dict()
        waiLowdict = dict()
        waiModdict = dict()
        waiSevdict = dict()
        waiCridict = dict()
        waiTotaldict = dict()
        opeLowdict = dict()
        opeModdict = dict()
        opeSevdict = dict()
        opeCridict = dict()
        opeTotaldict = dict()

        for i in range(0,int(args["scope"])):
                weeks.append(get_week_only(int(args["scope"])-1-i)) #set week list for images
                appNumberScandict[weeks[i]] = 0
                appOnboarddict[weeks[i]] = 0
                disLowdict[weeks[i]] = 0
                disModdict[weeks[i]] = 0
                disSevdict[weeks[i]] = 0
                disCridict[weeks[i]] = 0
                disTotaldict[weeks[i]] = 0
                fixLowdict[weeks[i]] = 0
                fixModdict[weeks[i]] = 0
                fixSevdict[weeks[i]] = 0
                fixCridict[weeks[i]] = 0
                fixTotaldict[weeks[i]] = 0
                waiLowdict[weeks[i]] = 0
                waiModdict[weeks[i]] = 0
                waiSevdict[weeks[i]] = 0
                waiCridict[weeks[i]] = 0
                waiTotaldict[weeks[i]] = 0
                opeLowdict[weeks[i]] = 0
                opeModdict[weeks[i]] = 0
                opeSevdict[weeks[i]] = 0
                opeCridict[weeks[i]] = 0
                opeTotaldict[weeks[i]] = 0
                
                
        if data is not None: #got data??#
                for app in data:
                        appName.append(app["applicationName"])
                        orgName.append(app["organizationName"])
                        # zeroed summary template.
                        s = get_aggs_list() 

                        for a in app["aggregations"]:
                                # process weekly reports for application.
                                process_week(a, s)

                        #calculate averages and totals.#
                        compute_summary(s)
                        app.update({"summary": s}) #just adding summary back to application for now.
                        app.update({"weeksInScope" : weeks})
                        app.update({"orgNames" : orgName})
                        app.update({"appNames" : appName})

                        
                        for i in range(int(app["summary"]["weeks"][0]),int(weeks[len(weeks)-1])+1):
                                if str(i) >= app["weeksInScope"][0]:
                                        appOnboarddict[str(i)] += 1
                                                
                        j = 0
                        for w in app["summary"]["weeks"]:
                                if w >= app["weeksInScope"][0]:
                                        appNumberScandict[w] += 1
                                        
                                        disLowdict[w] += app["summary"]["discoveredCounts"]["TOTAL"]["LOW"]["rng"][j]
                                        disModdict[w] += app["summary"]["discoveredCounts"]["TOTAL"]["MODERATE"]["rng"][j]
                                        disSevdict[w] += app["summary"]["discoveredCounts"]["TOTAL"]["SEVERE"]["rng"][j]
                                        disCridict[w] += app["summary"]["discoveredCounts"]["TOTAL"]["CRITICAL"]["rng"][j]
                                        disTotaldict[w] += app["summary"]["discoveredCounts"]["TOTAL"]["rng"][j]
                                        fixLowdict[w] += app["summary"]["fixedCounts"]["TOTAL"]["LOW"]["rng"][j]
                                        fixModdict[w] += app["summary"]["fixedCounts"]["TOTAL"]["MODERATE"]["rng"][j]
                                        fixSevdict[w] += app["summary"]["fixedCounts"]["TOTAL"]["SEVERE"]["rng"][j]
                                        fixCridict[w] += app["summary"]["fixedCounts"]["TOTAL"]["CRITICAL"]["rng"][j]
                                        fixTotaldict[w] += app["summary"]["fixedCounts"]["TOTAL"]["rng"][j]
                                        waiLowdict[w] += app["summary"]["waivedCounts"]["TOTAL"]["LOW"]["rng"][j]
                                        waiModdict[w] += app["summary"]["waivedCounts"]["TOTAL"]["MODERATE"]["rng"][j]
                                        waiSevdict[w] += app["summary"]["waivedCounts"]["TOTAL"]["SEVERE"]["rng"][j]
                                        waiCridict[w] += app["summary"]["waivedCounts"]["TOTAL"]["CRITICAL"]["rng"][j]
                                        waiTotaldict[w] += app["summary"]["waivedCounts"]["TOTAL"]["rng"][j]
                                        opeLowdict[w] += app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["LOW"]["rng"][j]
                                        opeModdict[w] += app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["MODERATE"]["rng"][j]
                                        opeSevdict[w] += app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["SEVERE"]["rng"][j]
                                        opeCridict[w] += app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["CRITICAL"]["rng"][j]
                                        opeTotaldict[w] += app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["rng"][j]
                                        #print(opeTotaldict)
                                        j += 1

                        appNumberScan = list(appNumberScandict.values())
                        appOnboard = list(appOnboarddict.values())
                        disTotal = list(disTotaldict.values())
                        fixTotal = list(fixTotaldict.values())
                        waiTotal = list(waiTotaldict.values())
                        opeTotal = list(opeTotaldict.values())
                        disLow = list(disLowdict.values())
                        disMod = list(disModdict.values())
                        disSev = list(disSevdict.values())
                        disCri = list(disCridict.values())
                        fixLow = list(fixLowdict.values())
                        fixMod = list(fixModdict.values())
                        fixSev = list(fixSevdict.values())
                        fixCri = list(fixCridict.values())
                        waiLow = list(waiLowdict.values())
                        waiMod = list(waiModdict.values())
                        waiSev = list(waiSevdict.values())
                        waiCri = list(waiCridict.values())
                        opeLow = list(opeLowdict.values())
                        opeMod = list(opeModdict.values())
                        opeSev = list(opeSevdict.values())
                        opeCri = list(opeCridict.values())
                        
                        
                        
                        app.update({"appNumberScan" : appNumberScan})
                        app.update({"appOnboard" : appOnboard})
                        app.update({"discoveredTotal" : disTotal})
                        app.update({"fixedTotal" : fixTotal})
                        app.update({"waivedTotal" : waiTotal})
                        app.update({"openTotal" : opeTotal})
                        app.update({"discoveredLow" : disLow})
                        app.update({"discoveredMod" : disMod})
                        app.update({"discoveredSev" : disSev})
                        app.update({"discoveredCri" : disCri})
                        app.update({"fixedLow" : fixLow})
                        app.update({"fixedMod" : fixMod})
                        app.update({"fixedSev" : fixSev})
                        app.update({"fixedCri" : fixCri})
                        app.update({"waivedLow" : waiLow})
                        app.update({"waivedMod" : waiMod})
                        app.update({"waivedSev" : waiSev})
                        app.update({"waivedCri" : waiCri})
                        app.update({"openLow" : opeLow})
                        app.update({"openMod" : opeMod})
                        app.update({"openSev" : opeSev})
                        app.update({"openCri" : opeCri})

        if args["pretty"]:
                print( json.dumps(data, indent=4) )

        if args["save"]:
                with open("successmetrics.json",'w') as f:
                        json.dump(data, f)
                        print( "saved to successmetrics.json" )

        #else:
                #print(data)

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
	r_body = {"timePeriod": "WEEK", "firstTimePeriod": get_week(scope) ,"lastTimePeriod": get_week(0), 
		"applicationIds": appId, "organizationIds": orgId}
	response = iq_session.post( url, json=r_body, headers=iq_header)
	return response.json()

def rnd(n): return round(n,2)
def avg(n): return rnd(sum(n)/len(n))
def rate(n, d): return 0 if d == 0 else (n/d)
def percent(n, d): return rnd(rate(n, d)*100)


def ms_days(v): #convert ms to days
	if v is None: return 0
	else: return round( v/86400000)


def get_aggs_list():
	s = {"weeks":[], "fixedRate":[], "waivedRate":[], "dealtRate":[]}
	s.update(dict.fromkeys(config["statRates"], 0))
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
