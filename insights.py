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
import json
from fpdf import FPDF
import datetime
import time
import plotly.graph_objects as go
import argparse

parser = argparse.ArgumentParser(description='generate insights report')
parser.add_argument('-all','--insights', help='generates insights report for all violations', action='store_true', required=False)
parser.add_argument('-s','--insightsSec', help='generates insights report only for Security violations', action='store_true', required=False)
parser.add_argument('-l','--insightsLic', help='generates insights report only for Licensing violations', action='store_true', required=False)
parser.add_argument('-before','--beforeFile', help='enter the path to the earlier json file to compare',dest='jsonBefore', action='store', required=True)
parser.add_argument('-after','--afterFile', help='enter the path to the later json file to compare',dest='jsonAfter', action='store', required=True)

args = vars(parser.parse_args())

xtitle = ["Date", "Applications", "Organisations"]
filenameBefore = args['jsonBefore']
filenameAfter = args['jsonAfter']
sonatype_colours = ['rgb(0,106,197)','rgb(253,198,22)','rgb(246,128,4)','rgb(205,0,40)']
disfixwai_colours = ['rgb(245,69,44)','rgb(0,209,146)','rgb(101,104,255)']
from datetime import date
today = datetime.datetime.today()
today = today.strftime("%Y-%m-%d %H:%M:%S")


with open(filenameBefore, 'r') as f1:
    report1 = json.load(f1)
    summary1 = report1["summary"]
    apps1 = report1["apps"]
    licences1 = report1["licences"]
    Security1 = report1["security"]
    appCount1 = len(apps1)

with open(filenameAfter, 'r') as f2:
    report2 = json.load(f2)
    summary2 = report2["summary"]
    apps2 = report2["apps"]
    licences2 = report2["licences"]
    Security2 = report2["security"]
    appCount2 = len(apps2)

#print(str(appCount1)+" , "+str(appCount2))

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
# Chart/pdf functions

def make_chart(period, data, filename, title, xtitle):
    fig = go.Figure(
        data=[ go.Bar(x=period, y=data, textposition='auto') ], 
        layout_title_text=title
    )

    fig.update_layout(autosize=False, width=864, height=528, xaxis=go.layout.XAxis(title_text=xtitle))
    fig.update_xaxes(tickvals=period,automargin=True)

    fig.write_image(filename)

def make_stacked_chart(period, data, legend, filename, title, xtitle,colours):
    traces = []
    for i in range(0, len(data)):
        trace = go.Bar(
            name = legend[i],
            x = period,
            y = data[i],
            textposition = 'auto',
            marker = dict(color=colours[i])
            )
        traces.append(trace)

    fig = go.Figure(data=traces, layout_title_text=title)
    fig.update_layout(
        barmode='stack',
        autosize=False,
        width=840,
        height=528,
        xaxis=go.layout.XAxis(
            title_text=xtitle
            )
        )
    fig.update_xaxes(tickvals=period,automargin=True)
    fig.write_image(filename)

def make_group_chart(period, data, legend, filename, title, xtitle,colours):
    traces = []
    for i in range(0, len(data)):
        trace = go.Bar(
            name = legend[i],
            x = period,
            y = data[i],
            textposition = 'auto',
            marker = dict(color=colours[i])
            )
        traces.append(trace)

    fig = go.Figure(data=traces, layout_title_text=title)
    fig.update_layout(
        barmode='group',
        autosize=False,
        width=840,
        height=528,
        xaxis=go.layout.XAxis(
            title_text=xtitle
            )
        )
    fig.update_xaxes(tickvals=period,automargin=True)
    fig.write_image(filename)



#---------------------------------

class PDF(FPDF):
    def header(self):
        # Logo
        self.image('sonatype_logo.png', 10, 8, 33)
        # Times bold 15
        self.set_font('Times', 'B', 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(100, 10, 'Success Metrics report', 1, 0, 'C')
        # Line break
        self.ln(20)

        # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Times', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

        #Chapter title
    def chapter_title(self, title):
        # Arial 12
        self.set_font('Times', 'B', 12)
        # Background color
        self.set_fill_color(200, 220, 255)
        # Title
        self.cell(0, 6, '%s' % (title), 0, 1, 'L', 1)
        # Line break
        self.ln(0)

        #Chapter body
    def chapter_body(self, content_dict):
        # Times 12
        self.set_font('Times', '', 12)
        # Output justified text
        #self.multi_cell(0, 5, content)
        for field in content_dict:
            self.cell(0, 5, field+": "+content_dict[field], 1, 1)
        # Line break
        self.ln()

        #Print chapter
    def print_chapter(self, title, content):
        self.add_page('L')
        self.chapter_title(title)
        self.chapter_body(content)

    def print_list(self,data):
        self.cell()

    def fancy_table(this,header,data):
        #Colors, line width and bold font
        this.set_fill_color(255,0,0)
        this.set_text_color(255)
        this.set_draw_color(128,0,0)
        this.set_line_width(.3)
        this.set_font('Times','B')
        #Header
        w=[]
        column_no = len(header)
        page_width = 277 #magic number for A4 in mm
        column_width = page_width/column_no
        for i in range(0,column_no):
            w.append(column_width)
        for i in range(0,column_no):
                this.cell(w[i],7,header[i],1,0,'C',1)
        this.ln()
        #Color and font restoration
        this.set_fill_color(224,235,255)
        this.set_text_color(0)
        this.set_font('Times')
        #Data
        fill=0
        #print("This data: ")
        #print(len(data))
        #print(len(w))
        #print(column_no)
        for row in data:
            for i in range(0,column_no):
                this.cell(w[i],6,row[i],'LR',0,'C',fill)
                #print(row[i])
            this.ln()
            fill=not fill
        this.cell(sum(w),0,'','T')


#---------------------------------

def output_pdf(pages, filename):
	pdf = FPDF()
	pdf.set_font('Times','B',12)
	for image in pages:
		pdf.add_page('L')
		pdf.set_xy(0,0)
		pdf.image(image, x = None, y = None, w = 0, h = 0, type = '', link = '')
	pdf.output(filename, 'F')


#---------------------------------

def nonzeroAvg(metric,percentage,integer):
    nonzero = 0
    aux = 0
    for i in range(0,len(metric)):
        if metric[i] != 0:
            aux += metric[i]
            nonzero += 1
    if nonzero == 0:
        nonzero = 1
    if percentage == True:
        output = round((aux / nonzero) * 100,1)
    elif integer == True:
        output = int(aux / nonzero)
    else:
        output = round(aux / nonzero,1)
    return(output)

#---------------------------------

def average(numerator,denominator,percentage,integer):
    if denominator == 0:
        denominator = 1
    if percentage == True:
        output = round((numerator / denominator) * 100,1)
    elif integer == True:
        output = int(numerator / denominator)
    else:
        output = round(numerator / denominator,1)
    return(output)
#---------------------------------

def weeksWithData(scope):
    aux = 0
    stop = 0
    for week in range(0,len(scope)):
        if scope[week] == 0 and stop == 0:
            aux += 1
        elif scope[week] != 0:
            stop = 1
    output = len(scope) - aux    
    return(output)

#---------------------------------

def getScope(scope1,scope2):
    index = scope2.index(scope1[-1])
    #print(index)
    scope = scope2[index+1:]
    #print(scope)
    return(scope)

#---------------------------------

#INSIGHTS: Insights report (comparison between two different json files)
def insights():

    pages, t, graphNo = [], 0, 1
    appName, orgName, OpeLow, OpeMod, OpeSev, OpeCri, mttrLow, mttrMod, mttrSev, mttrCri = [],[],[],[],[],[],[],[],[],[]
    printProgressBar(t,graphNo)
    
    pdf = PDF()
    pdf.alias_nb_pages()

    ################################
    #Loading data for json1 (before)
    ################################
    header_Open_App1 = ['Application', 'Critical','Severe','Moderate','Low']
    data_Open_App1= []
    for app in apps1:
        critical1 = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['CRITICAL']['rng'][-1]
        severe1 = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['SEVERE']['rng'][-1]
        moderate1 = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['MODERATE']['rng'][-1]
        low1 = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['LOW']['rng'][-1]
        aux1 = [critical1,severe1,moderate1,low1]
        data_Open_App1.append([app['applicationName']] + aux1)
    data_Open_App1.sort(key = lambda data_Open_App1: data_Open_App1[1], reverse = True)
    aux1=[]
    if len(data_Open_App1) <= 100:
        for i in range(0,len(data_Open_App1)):
            aux1.append([data_Open_App1[i][0],str(data_Open_App1[i][1]),str(data_Open_App1[i][2]),str(data_Open_App1[i][3]),str(data_Open_App1[i][4])])
    else:
        for i in range(0,100):
            aux1.append([data_Open_App1[i][0],str(data_Open_App1[i][1]),str(data_Open_App1[i][2]),str(data_Open_App1[i][3]),str(data_Open_App1[i][4])])
    data_Open_App1 = aux1
    ###########################

    ################################
    #Loading data for json2 (after)
    ################################
    header_Open_App2 = ['Application', 'Critical','Severe','Moderate','Low']
    data_Open_App2= []
    for app in apps2:
        critical2 = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['CRITICAL']['rng'][-1]
        severe2 = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['SEVERE']['rng'][-1]
        moderate2 = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['MODERATE']['rng'][-1]
        low2 = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['LOW']['rng'][-1]
        aux2 = [critical2,severe2,moderate2,low2]
        data_Open_App2.append([app['applicationName']] + aux2)
    data_Open_App2.sort(key = lambda data_Open_App2: data_Open_App2[1], reverse = True)
    aux2=[]
    if len(data_Open_App2) <= 100:
        for i in range(0,len(data_Open_App2)):
            aux2.append([data_Open_App2[i][0],str(data_Open_App2[i][1]),str(data_Open_App2[i][2]),str(data_Open_App2[i][3]),str(data_Open_App2[i][4])])
    else:
        for i in range(0,100):
            aux2.append([data_Open_App2[i][0],str(data_Open_App2[i][1]),str(data_Open_App2[i][2]),str(data_Open_App2[i][3]),str(data_Open_App2[i][4])])
    data_Open_App2 = aux2
    ###########################

    scope = getScope(summary1["dates"],summary2["dates"])  
    weeks = len(scope)
    weeks1 = weeksWithData(summary1["weeks"])
    weeks2 = weeksWithData(summary2["weeks"])

    onboarded = summary2["appOnboard"][-1] - summary1["appOnboard"][-1]
    onboarded1 = summary1["appOnboard"][-1]
    onboarded2 = summary2["appOnboard"][-1]
    weeklyOnboard = average(onboarded,weeks,0,0)
    weeklyOnboard1 = average(onboarded1,weeks1,0,0)
    weeklyOnboard2 = average(onboarded2,weeks2,0,0)

    scanned = sum(getScope(summary1["appNumberScan"],summary2["appNumberScan"]))
    scanned1 = sum(summary1["appNumberScan"])
    scanned2 = sum(summary2["appNumberScan"])
    weeklyScanned = average(scanned,weeks,0,0)
    weeklyScanned1 = average(scanned1,weeks1,0,0)

    scans = sum(summary2["weeklyScans"]) - sum(summary1["weeklyScans"])
    scans1 = sum(summary1["weeklyScans"])
    scans2 = sum(summary2["weeklyScans"])                
    weeklyScans = average(scans,weeks,0,0)
    weeklyScans1 = average(scans1,weeks1,0,0)
    weeklyScans2 = average(scans2,weeks2,0,0)

    discovered = sum(summary2["discoveredCounts"]["TOTAL"]) - sum(summary1["discoveredCounts"]["TOTAL"])
    discovered1 = sum(summary1["discoveredCounts"]["TOTAL"])
    discovered2 = sum(summary2["discoveredCounts"]["TOTAL"])
    disCri = sum(summary2["discoveredCounts"]["CRITICAL"]) - sum(summary1["discoveredCounts"]["CRITICAL"])
    disCri1 = sum(summary1["discoveredCounts"]["CRITICAL"])
    disCri2 = sum(summary2["discoveredCounts"]["CRITICAL"])
    
    if len(data_Open_App1) > 0:
        mostCri = data_Open_App2[0][0]
        mostCriVal = data_Open_App2[0][1]
    else:
        mostCri = "Error: No applications found!"
        mostCriVal = 0
    if len(data_Open_App2) > 0:
        leastCri = data_Open_App2[-1][0]
        leastCriVal = data_Open_App2[-1][1]
    else:
        leastCri = "Error: No applications found!"
        leastCriVal = 0

    fixed = sum(summary2["fixedCounts"]["TOTAL"]) - sum(summary1["fixedCounts"]["TOTAL"])
    fixed1 = sum(summary1["fixedCounts"]["TOTAL"])
    fixed2 sum(summary2["fixedCounts"]["TOTAL"])
    fixCri =
    fixCri1 =
    fixCri2 = 

    waived = sum(summary2["waivedCounts"]["TOTAL"]) - sum(summary1["waivedCounts"]["TOTAL"])
    waived1 = sum(summary1["waivedCounts"]["TOTAL"])
    waived2 = sum(summary2["waivedCounts"]["TOTAL"])
    waivedCri = 
    waivedCri1 = 
    waivedCri2 = 
    
    dealt = fixed + waived
    if discovered > 0:
        dealtRate = round((dealt / discovered) * 100,1)
    else:
        dealtRate = 0
        
    riskRatio = [float(i) for i in summary2["riskRatioCritical"]]
    riskRatio = riskRatio[-weeks:]
    riskRatioAvg = average(sum(riskRatio),weeks,0,0)
    
    mttr = summary2["mttrCriticalThreat"][-weeks:]
    mttrAvg = nonzeroAvg(mttr,0,0)



    pdf.print_chapter('Insights Summary (all violations)',"")
    
    content0 = "Report run on: "+str(today)+" comparing "+str(filenameBefore)+" with "+str(filenameAfter)+" from w/c "+str(scope[0])+" to w/c "+str(scope[-1])
    pdf.multi_cell(0,5,content0,0)
    pdf.ln(10)
    
    content1 = "During the "+str(weeks)+" weeks in scope, your organisation:"
    pdf.set_font('Times', 'B', 24)
    pdf.cell(0,0,content1,0)
    pdf.ln(10)
    pdf.set_font('Times', 'B', 18)
    
    content2 = "Onboarded "+str(onboarded)+" applications (going from "+str(onboarded1)+" to "+str(onboarded2)+" apps), at an average of "+str(weeklyOnboard)+" per week (previously "+str(weeklyOnboard1)+" apps onboarded per week)."
    pdf.multi_cell(0,7,content2,0)
    pdf.ln(1)
    if weeklyOnboard > weeklyOnboard1:
        content21 = "This represents a "+str(average(weeklyOnboard,weeklyOnboard1,1,0) - 100)+"% increase in the onboarding rate."
        pdf.set_text_color(0, 153, 0)
        pdf.multi_cell(0,7,content21,0)
    elif weeklyOnboard < weeklyOnboard1:
        content21 = "This represents a "+str(100 - average(weeklyOnboard,weeklyOnboard1,1,0))+"% reduction in the onboarding rate. Have all apps been onboarded yet?"
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0,7,content21,0)
    elif onboarded1 == onboarded2:
        content21 = "No new applications have been onboarded during this time period. Have all apps been onboarded yet?"
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0,7,content21,0)
    else:
        content21 = "This represents a stable onboarding pattern."
        pdf.set_text_color(0, 0, 255)
        pdf.multi_cell(0,7,content21,0)
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)

    content3 = "Scanned applications at an average of "+str(weeklyScanned)+" apps scanned per week (previously "+str(weeklyScanned1)+" apps scanned per week). Scanning coverage is "+str(average(weeklyScanned,onboarded2,1,0))+"% (percentage of total apps scanned)."
    pdf.multi_cell(0,7,content3,0)
    pdf.ln(1)
    if weeklyScanned > weeklyScanned1:
        content31 = "This represents a "+str(average(weeklyScanned,weeklyScanned1,1,0) - 100)+"% increase in the scanning coverage rate."
        pdf.set_text_color(0, 153, 0)
        pdf.multi_cell(0,7,content31,0)
    elif weeklyScanned < weeklyScanned1:
        content31 = "This represents a "+str(100 - average(weeklyScanned,weeklyScanned1,1,0))+"% reduction in the scanning coverage rate."
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0,7,content31,0)
    elif scanned == 0:
        content31 = "No applications have been scanned during this time period. Is there a problem with the CI integration or with the uptake of IQ within the development teams?"
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0,7,content31,0)
    else:
        content31 = "This represents a stable app scanning pattern."
        pdf.set_text_color(0, 0, 255)
        pdf.multi_cell(0,7,content31,0)
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
        
    content4 = "Performed "+str(scans)+" scans at an average of "+str(weeklyScans)+" scans per week (previously "+str(weeklyScans1)+" scans per week)."
    pdf.multi_cell(0,7,content4,0)
    pdf.ln(1)
    if weeklyScans > weeklyScans1:
        content41 = "This represents a "+str(round(average(weeklyScans,weeklyScans1,1,0) - 100,1))+"% increase in the scanning rate."
        pdf.set_text_color(0, 153, 0)
        pdf.multi_cell(0,7,content41,0)
    elif weeklyScans < weeklyScans1:
        content41 = "This represents a "+str(100 - average(weeklyScans,weeklyScans1,1,0))+"% reduction in the scanning rate."
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0,7,content41,0)
    elif scans == 0:
        content41 = "No scans have been performed during this time period. Is there a problem with the CI integration or with the uptake of IQ within the development teams?"
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0,7,content41,0)
    else:
        content41 = "This represents a stable scanning pattern."
        pdf.set_text_color(0, 0, 255)
        pdf.multi_cell(0,7,content41,0)
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    
    content5 = "Discovered "+str(discovered)+" new violations (previously "+str(discovered1)+" violations). Of these, "+str(disCri)+" were Critical (previously "+str(disCri1)+" were Critical)."
    pdf.multi_cell(0,7,content5,0)
    pdf.ln(1)
    if discovered > discovered1:
        content51 = "This represents a "+str(round(average(discovered,discovered1,1,0) - 100,1))+"% increase in the discovery rate. This could indicate that development teams are not selecting safer OSS components. Have you integrated the IDE plugins and Chrome extension?"
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0,7,content51,0)
    elif discovered < discovered1:
        content51 = "This represents a "+str(100 - average(discovered,discovered1,1,0))+"% reduction in the discovery rate. This could indicate that development teams are selecting safer OSS components, hence shifting left."
        pdf.set_text_color(0, 153, 0)
        pdf.multi_cell(0,7,content51,0)
    elif discovered == 0 and scans != 0:
        content51 = "No new discovered violations during this time period. This could indicate that development teams are selecting safer OSS components, hence shifting left."
        pdf.set_text_color(0, 153, 0)
        pdf.multi_cell(0,7,content51,0)
    else:
        content51 = "This represents a stable discovery rate."
        pdf.set_text_color(0, 0, 255)
        pdf.multi_cell(0,7,content51,0)
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)

    content6 = "Fixed "+str(fixed)+" new violations (previously "+str(fixed1)+" violations). Of these, "+str(disCri)+" were Critical (previously "+str(disCri1)+" were Critical)."
    pdf.multi_cell(0,7,content6,0)
    pdf.ln(1)
    if fixed > fixed1:
        content61 = "This represents a "+str(round(average(fixed,fixed1,1,0) - 100,1))+"% increase in the discovery rate. This could indicate that development teams are not selecting safer OSS components. Have you integrated the IDE plugins and Chrome extension?"
        pdf.set_text_color(255, 0, 0)
        pdf.multi_cell(0,7,content61,0)
    elif fixed < fixed1:
        content61 = "This represents a "+str(100 - average(fixed,fixed1,1,0))+"% reduction in the discovery rate. This could indicate that development teams are selecting safer OSS components, hence shifting left."
        pdf.set_text_color(0, 153, 0)
        pdf.multi_cell(0,7,content61,0)
    elif fixed == 0 and scans != 0:
        content61 = "No new fixed violations during this time period. This could indicate that development teams are selecting safer OSS components, hence shifting left."
        pdf.set_text_color(0, 153, 0)
        pdf.multi_cell(0,7,content61,0)
    else:
        content61 = "This represents a stable discovery rate."
        pdf.set_text_color(0, 0, 255)
        pdf.multi_cell(0,7,content61,0)
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)

    
    content6 = "Fixed "+str(fixed)+" and waived "+str(waived)+" violations from your open backlog"
    content7 = "\t  Which means that your Fixing Rate (Fixed & Waived / Discovered) is "+str(dealtRate)+"%"
    content8 = "\t- On average, each application has "+str(riskRatioAvg)+" Open Critical violations"
    content9 = "\t\t\t Most Criticals: "+str(mostCri)+" with "+str(mostCriVal)+" Critical violations"
    content10 = "\t\t\t Least Criticals: "+str(leastCri)+" with "+str(leastCriVal)+" Critical violations"
    content11 = "\t- It took an average of "+str(mttrAvg)+" days to fix Critical violations"



    

    pdf.cell(0,0,content6,0)
    pdf.ln(10)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(0,0,content7,0)
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0,0,content8,0)
    pdf.ln(10)
    pdf.cell(0,0,content9,0)
    pdf.ln(10)
    pdf.cell(0,0,content10,0)
    pdf.ln(15)
    pdf.cell(0,0,content11,0)

    t +=1
    printProgressBar(t,graphNo)

    ###########################

    
    #-------------------------------------------------------------------------
    pdf.output('./output/insights_report.pdf', 'F')


#-------------------------------------------------------------------------
def insightsSec():
    print("Report not yet implemented")
#-------------------------------------------------------------------------
def insightsLic():
    print("Report not yet implemented")
#-------------------------------------------------------------------------
#-------------------------------------------------------------------------


def main():
    
    for report in args:
        if args[report] == True:
            exec(report+"()")
           

if __name__ == "__main__":
    main()
#raise SystemExit

