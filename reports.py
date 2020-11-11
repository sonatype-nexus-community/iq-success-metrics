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

today = datetime.datetime.today()
today = today.strftime("%Y-%m-%d")

parser = argparse.ArgumentParser(description='get some reports')
parser.add_argument('-e','--executiveAll', help='generates executive report for all violations', action='store_true', required=False)
parser.add_argument('-es','--executiveSec', help='generates executive report only for Security violations', action='store_true', required=False)
parser.add_argument('-el','--executiveLic', help='generates executive report only for Licensing violations', action='store_true', required=False)
parser.add_argument('-t','--tablesAll', help='generates a report in table format for all violations', action='store_true', required=False)
parser.add_argument('-ts','--tablesSec', help='generates a report in table format only for Security violations', action='store_true', required=False)
parser.add_argument('-tl','--tablesLic', help='generates a report in table format only for Licensing violations', action='store_true', required=False)
parser.add_argument('-f','--file', help='input file', default='./output/'+str(today)+'_successmetrics.json',dest='jsonFile', action='store', required=False)

args = vars(parser.parse_args())

xtitle = ["Date", "Applications", "Organisations"]
filename = args['jsonFile']
sonatype_colours = ['rgb(0,106,197)','rgb(253,198,22)','rgb(246,128,4)','rgb(205,0,40)']
disfixwai_colours = ['rgb(245,69,44)','rgb(0,209,146)','rgb(101,104,255)']
from datetime import date
today = datetime.datetime.today()


with open(filename, 'r') as f:
    report = json.load(f)
    summary = report["summary"]
    apps = report["apps"]
    licences = report["licences"]
    Security = report["security"]
    appCount = len(apps)

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
        self.ln(4)

        #Chapter body
    def chapter_body(self, content_dict):
        # Times 12
        self.set_font('Times', '', 12)
        # Output justified text
        #self.multi_cell(0, 5, content)
        for field in content_dict:
            self.cell(0, 10, field+": "+content_dict[field], 1, 1)
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

#EXECUTIVE: Executive summary report (combination of reports but without going into app level)
def executive(apps, summary, report):

    pages, t, graphNo = [], 0, 17
    appName, orgName, OpeLow, OpeMod, OpeSev, OpeCri, mttrLow, mttrMod, mttrSev, mttrCri = [],[],[],[],[],[],[],[],[],[]
    printProgressBar(t,graphNo)
    
    pdf = PDF()
    pdf.alias_nb_pages()

    if report == 'summary':
        selector = 'TOTAL'
    if report == 'security':
        selector = 'SECURITY'
    if report == 'licences':
        selector = 'LICENSE'

    ###########################
    header_Open_App = ['Application', 'Critical','Severe','Moderate','Low']
    data_Open_App= []
    for app in apps:
        critical = app[report]['openCountsAtTimePeriodEnd'][selector]['CRITICAL']['rng'][-1]
        severe = app[report]['openCountsAtTimePeriodEnd'][selector]['SEVERE']['rng'][-1]
        moderate = app[report]['openCountsAtTimePeriodEnd'][selector]['MODERATE']['rng'][-1]
        low = app[report]['openCountsAtTimePeriodEnd'][selector]['LOW']['rng'][-1]
        aux = [critical,severe,moderate,low]
        data_Open_App.append([app['applicationName']] + aux)
    data_Open_App.sort(key = lambda data_Open_App: data_Open_App[1], reverse = True)
    aux=[]
    if len(data_Open_App) <= 100:
        for i in range(0,len(data_Open_App)):
            aux.append([data_Open_App[i][0],str(data_Open_App[i][1]),str(data_Open_App[i][2]),str(data_Open_App[i][3]),str(data_Open_App[i][4])])
    else:
        for i in range(0,100):
            aux.append([data_Open_App[i][0],str(data_Open_App[i][1]),str(data_Open_App[i][2]),str(data_Open_App[i][3]),str(data_Open_App[i][4])])
    data_Open_App = aux

    ###########################
    
    weeks = len(summary["weeks"])
    scope = weeksWithData(summary["appOnboard"])
    onboarded = summary["appOnboard"][-1] - summary["appOnboard"][0]
    total_onboarded = summary["appOnboard"][-1]
    weeklyOnboard = average(onboarded,scope,0,0)
    scanned = sum(summary["appNumberScan"])
    weeklyScanned = average(scanned,scope,0,0)
    scans = sum(summary["weeklyScans"])
    weeklyScans = average(scans,scope,0,0)
    discovered = sum(summary["discoveredCounts"]["TOTAL"])
    disCri = sum(summary["discoveredCounts"]["CRITICAL"])
    if len(data_Open_App) > 0:
        mostCri = data_Open_App[0][0]
        mostCriVal = data_Open_App[0][1]
    else:
        mostCri = "Error: No applications found!"
        mostCriVal = 0
    if len(data_Open_App) > 0:
        leastCri = data_Open_App[-1][0]
        leastCriVal = data_Open_App[-1][1]
    else:
        leastCri = "Error: No applications found!"
        leastCriVal = 0
    fixed = sum(summary["fixedCounts"]["TOTAL"])
    fixedCri = sum(summary["fixedCounts"]["CRITICAL"])
    waived = sum(summary["waivedCounts"]["TOTAL"])
    waivedCri = sum(summary["waivedCounts"]["CRITICAL"])
    opened = summary["openCountsAtTimePeriodEnd"]["TOTAL"][-1]
    openedCri = summary["openCountsAtTimePeriodEnd"]["CRITICAL"][-1]

    dealt = fixed + waived
    if discovered > 0:
        dealtRate = round((dealt / discovered) * 100,1)
    else:
        dealtRate = 0
    riskRatio = [float(i) for i in summary["riskRatioCritical"]]
    riskRatioAvg = average(sum(riskRatio),scope,0,0)
    mttrAvg = nonzeroAvg(summary["mttrCriticalThreat"],0,0)
    content0 = "Report run on: "+str(today)
    content1 = "During the "+str(weeks)+" weeks in scope, your organisation:"
    content2 = "\t- Onboarded "+str(onboarded)+" applications (for a total of "+str(total_onboarded)+"), at an average of "+str(weeklyOnboard)+" per week."
    content3 = "\t- Scanned applications at an average of "+str(weeklyScanned)+" apps scanned per week."
    content4 = "\t- Performed "+str(scans)+" scans at an average of "+str(weeklyScans)+" scans per week."
    content5 = "\t- Discovered "+str(discovered)+" new violations ("+str(disCri)+" of them Critical)."
    content6 = "\t- Fixed "+str(fixed)+" ("+str(fixedCri)+" of them Critical) and waived "+str(waived)+" violations ("+str(waivedCri)+" of them Critical) from your open backlog."
    content71 = "\t- Your organisation currently has "+str(opened)+" open violations in their backlog. Of these, "+str(openedCri)+" were Critical."
    content7 = "\t  Which means that your Backlog Dealing Rate (Fixed & Waived / Discovered) is "+str(dealtRate)+"%"
    content8 = "\t- On average, each application has "+str(riskRatioAvg)+" Open Critical violations"
    content9 = "\t\t\t Most Criticals: "+str(mostCri)+" with "+str(mostCriVal)+" Critical violations"
    content10 = "\t\t\t Least Criticals: "+str(leastCri)+" with "+str(leastCriVal)+" Critical violations"
    content11 = "\t- It took an average of "+str(mttrAvg)+" days to fix Critical violations"

    if report == 'summary':
        pdf.print_chapter('Outcomes Summary (all violations)',"")
    elif report == 'security':
        pdf.print_chapter('Outcomes Summary (only security violations)',"")
    elif report =='licences':
        pdf.print_chapter('Outcomes Summary (only licensing violations)',"")
    
    pdf.cell(0,0,content0,0)
    pdf.ln(10)
    pdf.set_font('Times', 'B', 24)
    pdf.cell(0,0,content1,0)
    pdf.ln(15)
    pdf.set_font('Times', 'B', 18)
    pdf.cell(0,0,content2,0)
    pdf.ln(10)
    pdf.cell(0,0,content3,0)
    pdf.ln(10)
    pdf.cell(0,0,content4,0)
    pdf.ln(10)
    pdf.cell(0,0,content5,0)
    pdf.ln(7)
    pdf.multi_cell(0,7,content6,0)
    pdf.ln(5)
    pdf.multi_cell(0,7,content71,0)
    pdf.ln(5)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(0,0,content7,0)
    pdf.ln(10)
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
    pdf.print_chapter('Number of apps onboarded (weekly view)',"")
    make_chart( 
        summary['timePeriodStart'], 
        summary['appOnboard'], 
        "./output/AppsOnboarded.png", 
        "Number of apps onboarded (weekly view)", 
        xtitle[0])
    pdf.image("./output/AppsOnboarded.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #-------------------------------------------------------------------------
    #------------------------------------
    pdf.print_chapter('Number of scanned apps per week',"")
    make_chart(
        summary['timePeriodStart'], 
        summary['appNumberScan'], 
        "./output/AppsScanning.png", 
        "Number of apps scanned per week", 
        xtitle[0]
    )
    pdf.image("./output/AppsScanning.png",10,36,270)
    t +=1
    printProgressBar(t, graphNo)
    #------------------------------------
    
    pdf.print_chapter('Number of scans per week',"")
    make_chart( 
        summary['timePeriodStart'], 
        summary['weeklyScans'], 
        "./output/WeeklyScans.png", 
        "Total number of scans per week", 
        xtitle[0])
    pdf.image("./output/WeeklyScans.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)

    #-------------------------------------------------------------------------
    header_most_scanned = ['Application','Total number of scans']
    data_most_scanned, aux = [],[]
    for app in apps:
        appName = app["applicationName"]
        scans = sum(app[report]["evaluationCount"]["rng"])
        aux = [appName,scans]
        data_most_scanned.append(aux)
    data_most_scanned.sort(key = lambda data_most_scanned: data_most_scanned[1], reverse = True)
    aux = []
    if len(data_most_scanned) <= 100:
        for i in range(0,len(data_most_scanned)):
            aux.append([data_most_scanned[i][0],str(data_most_scanned[i][1])])
    else:
        for i in range(0,100):
            aux.append([data_most_scanned[i][0],str(data_most_scanned[i][1])])
    data_most_scanned = aux
    pdf.print_chapter('Top 100 most scanned applications','')
    pdf.fancy_table(header_most_scanned, data_most_scanned)
    t +=1
    printProgressBar(t,graphNo)

    #-------------------------------------------------------------------------

    if report == 'summary':
        pdf.print_chapter('Current open backlog for all violations', "")
        content = "Number of open violations (backlog) per week for all violations"
    elif report == 'security':
        pdf.print_chapter('Current open backlog for security violations only', "")
        content = "Number of open violations (backlog) per week for security violations only"
    elif report =='licences':
        pdf.print_chapter('Current open backlog for licensing violations only', "")
        content = "Number of open violations (backlog) per week for licensing violations only"

    make_stacked_chart(
        summary['timePeriodStart'],
        summary['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/OpenBacklog.png",
        content,
        xtitle[0],sonatype_colours)
    pdf.image("./output/OpenBacklog.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------

    if report == 'summary':
        pdf.print_chapter('Current risk per application sorted by criticality for all violations (Top 100)', "")
    elif report == 'security':
        pdf.print_chapter('Current risk per application sorted by criticality for security violations only (Top 100)', "")
    elif report =='licences':
        pdf.print_chapter('Current risk per application sorted by criticality for licensing violations only (Top 100)', "")
    pdf.fancy_table(header_Open_App, data_Open_App)
    t +=1
    printProgressBar(t,graphNo)

#---------------------------------------------------------------------
 


    #---------------------------------------------------------------------
    if report == 'summary':
        pdf.print_chapter('Current Total Number of Open violations by organisation for all violations', "")
        content = "Current Total Number of Open violations by organisation for all violations"
    elif report == 'security':
        pdf.print_chapter('Current Total Number of Open violations by organisation for security violations only', "")
        content = "Current Total Number of Open violations by organisation for security violations only"
    elif report =='licences':
        pdf.print_chapter('Current Total Number of Open violations by organisation for licensing violations only', "")
        content = "Current Total Number of Open violations by organisation for licensing violations only"
    for app in apps:
        orgName.append(app["organizationName"])
        OpeLow.append(app[report]["openCountsAtTimePeriodEnd"][selector]["LOW"]["rng"][len(app[report]["openCountsAtTimePeriodEnd"][selector]["LOW"]["rng"])-1])
        OpeMod.append(app[report]["openCountsAtTimePeriodEnd"][selector]["MODERATE"]["rng"][len(app[report]["openCountsAtTimePeriodEnd"][selector]["MODERATE"]["rng"])-1])
        OpeSev.append(app[report]["openCountsAtTimePeriodEnd"][selector]["SEVERE"]["rng"][len(app[report]["openCountsAtTimePeriodEnd"][selector]["SEVERE"]["rng"])-1])
        OpeCri.append(app[report]["openCountsAtTimePeriodEnd"][selector]["CRITICAL"]["rng"][len(app[report]["openCountsAtTimePeriodEnd"][selector]["CRITICAL"]["rng"])-1])
    
    make_stacked_chart(
        orgName,
        [
            OpeLow,
            OpeMod,
            OpeSev,
            OpeCri
        ],
       ['Low', 'Moderate', 'Severe', 'Critical'],
       "./output/Current_Open_Orgs.png", 
       content,
        xtitle[2],sonatype_colours
    )

    orgs = []
    orgsLow, orgsMod, orgsSev, orgsCri = {},{},{},{}
    for i in range(0,len(orgName)):
        if orgName[i] not in orgs:
            orgs.append(orgName[i])
            orgsLow[orgName[i]]=OpeLow[i]
            orgsMod[orgName[i]]=OpeMod[i]
            orgsSev[orgName[i]]=OpeSev[i]
            orgsCri[orgName[i]]=OpeCri[i]
        elif orgName[i] in orgs:
            orgsLow[orgName[i]]+=OpeLow[i]
            orgsMod[orgName[i]]+=OpeMod[i]
            orgsSev[orgName[i]]+=OpeSev[i]
            orgsCri[orgName[i]]+=OpeCri[i]
            
    #print("Orgs",orgs)
    #print("Critical",orgsCri)
    pdf.image("./output/Current_Open_Orgs.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------

###########################
    header_Open_Org = ['Organisation', 'Critical','Severe','Moderate','Low']
    data_Open_Org= []
    for org in orgs:
        critical = orgsCri[org]
        severe = orgsSev[org]
        moderate = orgsMod[org]
        low = orgsLow[org]
        aux = [critical,severe,moderate,low]
        data_Open_Org.append([org] + aux)
    data_Open_Org.sort(key = lambda data_Open_Org: data_Open_Org[1], reverse = True)
    aux=[]
    if len(data_Open_Org) <= 100:
        for i in range(0,len(data_Open_Org)):
            aux.append([data_Open_Org[i][0],str(data_Open_Org[i][1]),str(data_Open_Org[i][2]),str(data_Open_Org[i][3]),str(data_Open_Org[i][4])])
    else:
        for i in range(0,100):
            aux.append([data_Open_Org[i][0],str(data_Open_Org[i][1]),str(data_Open_Org[i][2]),str(data_Open_Org[i][3]),str(data_Open_Org[i][4])])
    data_Open_Org = aux

    ###########################
    
    if report == 'summary':
        pdf.print_chapter('Current Total Number of Open violations per Org sorted by criticality for all violations (Top 100)', "")
    elif report == 'security':
        pdf.print_chapter('Current Total Number of Open violations per Org sorted by criticality for security violations only (Top 100)', "")
    elif report =='licences':
        pdf.print_chapter('Current Total Number of Open violations per Org sorted by criticality for licensing violations only (Top 100)', "")
    pdf.fancy_table(header_Open_Org, data_Open_Org)
    t +=1
    printProgressBar(t,graphNo)

#---------------------------------------------------------------------    
   
    if report == 'summary':
        pdf.print_chapter('Total Number of Discovered, Fixed & Waived violations week-on-week (all violations)', "")
        content = "Total Number of Discovered, Fixed & Waived violations week-on-week (all violations)"
    elif report == 'security':
        pdf.print_chapter('Total Number of Discovered, Fixed & Waived violations week-on-week (security only)', "")
        content = "Total Number of Discovered, Fixed & Waived violations week-on-week (security violations only)"
    elif report =='licences':
        pdf.print_chapter('Total Number of Discovered, Fixed & Waived violations week-on-week (licensing only)', "")
        content = "Total Number of Discovered, Fixed & Waived violations week-on-week (licensing violations only)"
    make_group_chart(
        summary['timePeriodStart'],
        [
            summary['discoveredCounts']['TOTAL'],
            summary['fixedCounts']['TOTAL'],
            summary['waivedCounts']['TOTAL']
        ],
       ['Discovered', 'Fixed', 'Waived'],
       "./output/Total_DisFixWaiCount.png", 
       content,
        xtitle[0],disfixwai_colours
    )
    pdf.image("./output/Total_DisFixWaiCount.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    if report == 'summary':
        pdf.print_chapter('Total Number of Discovered violations by severity week-on-week (all violations)', "")
        content = "Total Number of Discovered violations by severity week-on-week (all violations)"
    elif report == 'security':
        pdf.print_chapter('Total Number of Discovered violations by severity week-on-week (security violations only)', "")
        content = "Total Number of Discovered violations by severity week-on-week (security violations only)"
    elif report =='licences':
        pdf.print_chapter('Total Number of Discovered violations by severity week-on-week (licensing violations only)', "")
        content = "Total Number of Discovered violations by severity week-on-week (licensing violations only)"
    make_stacked_chart(
        summary['timePeriodStart'], 
        summary['discoveredCounts']['LIST'],
        ['Discovered Low', 'Discovered Moderate', 'Discovered Severe', 'Discovered Critical'],
        "./output/Discovered_breakdown.png",
        content,
        xtitle[0],sonatype_colours
    )
    pdf.image("./output/Discovered_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    if report == 'summary':
        pdf.print_chapter('Total Number of Fixed violations by severity week-on-week (all violations)', "")
        content = "Total Number of Fixed violations by severity week-on-week (all violations)"
    elif report == 'security':
        pdf.print_chapter('Total Number of Fixed violations by severity week-on-week (security violations only)', "")
        content = "Total Number of Fixed violations by severity week-on-week (security violations only)"
    elif report =='licences':
        pdf.print_chapter('Total Number of Fixed violations by severity week-on-week (licensing violations only)', "")
        content = "Total Number of Fixed violations by severity week-on-week (licensing violations only)"
    make_stacked_chart(
        summary['timePeriodStart'], 
        summary['fixedCounts']['LIST'],
        ['Fixed Low', 'Fixed Moderate', 'Fixed Severe', 'Fixed Critical'],
        "./output/Fixed_breakdown.png",
        content,
        xtitle[0],sonatype_colours
    )
    pdf.image("./output/Fixed_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    if report == 'summary':
        pdf.print_chapter('Total Number of Waived violations by severity week-on-week (all violations)', "")
        content = "Total Number of Waived violations by severity week-on-week (all violations)"
    elif report == 'security':
        pdf.print_chapter('Total Number of Waived violations by severity week-on-week (security violations only)', "")
        content = "Total Number of Waived violations by severity week-on-week (security violations only)"
    elif report =='licences':
        pdf.print_chapter('Total Number of Waived violations by severity week-on-week (licensing violations only)', "")
        content = "Total Number of Waived violations by severity week-on-week (licensing violations only)"
    make_stacked_chart(
        summary['timePeriodStart'], 
        summary['waivedCounts']['LIST'],
        ['Waived Low', 'Waived Moderate', 'Waived Severe', 'Waived Critical'],
        "./output/Waived_breakdown.png",
        content,
        xtitle[0],sonatype_colours
    )

    pdf.image("./output/Waived_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
     #---------------------------------------------------------------------
    '''
    make_chart( 
        summary['timePeriodStart'], 
        summary['mttrLowThreat'], 
        "./output/MTTR_Low.png", 
        "MTTR (in days) for all Low Threat violations week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Low Threat violations week-on-week','')
    pdf.image('./output/MTTR_Low.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        summary['timePeriodStart'], 
        summary['mttrModerateThreat'], 
        "./output/MTTR_Moderate.png", 
        "MTTR (in days) for all Moderate Threat violations week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Moderate Threat violations week-on-week','')
    pdf.image('./output/MTTR_Moderate.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
    '''

     #---------------------------------------------------------------------
    make_chart( 
        summary['timePeriodStart'], 
        summary['mttrCriticalThreat'], 
        "./output/MTTR_Critical.png", 
        "MTTR (in days) for all Critical Threat violations week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Critical Threat violations week-on-week','')
    pdf.image('./output/MTTR_Critical.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
    #---------------------------------------------------------------------

     #---------------------------------------------------------------------
    make_chart( 
        summary['timePeriodStart'], 
        summary['mttrSevereThreat'], 
        "./output/MTTR_Severe.png", 
        "MTTR (in days) for all Severe Threat violations week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Severe Threat violations week-on-week','')
    pdf.image('./output/MTTR_Severe.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)


#-------------------------------------------------------------------------
    if report == 'summary':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) for Critical violations (all violations)', "")
    elif report == 'security':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) for Critical violations (security violations only)', "")
    elif report =='licences':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) for Critical violations (licensing violations only)', "")
    make_chart( 
        summary['timePeriodStart'], 
        summary['riskRatioCritical'], 
        "./output/riskRatioCritical.png", 
        "Risk Ratio for Critical violations (weekly view)", 
        xtitle[0])
    pdf.image("./output/riskRatioCritical.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
#-------------------------------------------------------------------------

#-------------------------------------------------------------------------
    if report == 'summary':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) for Severe violations (all violations)', "")
    elif report == 'security':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) for Severe violations (security violations only)', "")
    elif report =='licences':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) for Severe violations (licensing violations only)', "")
    make_chart( 
        summary['timePeriodStart'], 
        summary['riskRatioSevere'], 
        "./output/riskRatioSevere.png", 
        "Risk Ratio for Severe violations (weekly view)", 
        xtitle[0])
    pdf.image("./output/riskRatioSevere.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
#-------------------------------------------------------------------------

    '''
#-------------------------------------------------------------------------
    if len(summary['timePeriodStart']) >= 4:
        header_riskRatio = ['Risk Ratio', summary['timePeriodStart'][-4], summary['timePeriodStart'][-3], summary['timePeriodStart'][-2], summary['timePeriodStart'][-1]]
        shift = [-4,-3,-2,-1]
    else:
        header_riskRatio = ['Risk Ratio']
        shift = []
        for k in range(0,len(summary['timePeriodStart'])):
            header_riskRatio.append(summary['timePeriodStart'][k - len(summary['timePeriodStart'])])
            shift.append(k - len(summary['timePeriodStart']))
    levels = ['Critical','Severe','Moderate','Low']
    measures = ['riskRatioCritical','riskRatioSevere','riskRatioModerate','riskRatioLow']
    data_riskRatio= []
    for i in range(0,len(levels)):
        data_riskRatio.append([levels[i]])
        for j in range(0, len(shift)):
            data_riskRatio[i].append(str(summary[measures[i]][shift[j]]))

    if report == 'summary':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (all violations)', "")
    elif report == 'security':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (security violations only)', "")
    elif report =='licences':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (licensing violations only)', "")
    pdf.fancy_table(header_riskRatio, data_riskRatio)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
'''

    #-------------------------------------------------------------------------
    return pdf


#-------------------------------------------------------------------------

def executiveAll():
    pdf = executive(apps, summary, 'summary')
    pdf.output('./output/executive_report.pdf','F')

def executiveSec():
    pdf = executive(apps, Security,'security')
    pdf.output('./output/executive_security_report.pdf', 'F')

def executiveLic():
    pdf = executive(apps, licences, 'licences')
    pdf.output('./output/executive_licensing_report.pdf','F')

def tablesAll():
    pdf = tables(apps, summary, 'summary')
    pdf.output('./output/tables_report.pdf','F')

def tablesSec():
    pdf = tables(apps, Security, 'security')
    pdf.output('./output/tables_security_report.pdf','F')

def tablesLic():
    pdf = tables(apps, licences, 'licences')
    pdf.output('./output/tables_licensing_report.pdf','F')

#-------------------------------------------------------------------------
#TABLES: "To provide a report for all violations, in table format to accommodate for customers with thousands of applications"
#-------------------------------------------------------------------------
    
def tables(apps, summary, report):
    pages, t, graphNo = [], 0, 7
    printProgressBar(t,graphNo)
    
    pdf = PDF()
    pdf.alias_nb_pages()

    if report == 'summary':
        selector = 'TOTAL'
    if report == 'security':
        selector = 'SECURITY'
    if report == 'licences':
        selector = 'LICENSE'
    
    #-------------------------------------------------------------------------
    pdf.print_chapter('Number of apps onboarded (weekly view)',"")
    make_chart( 
        summary['timePeriodStart'], 
        summary['appOnboard'], 
        "./output/AppsOnboarded.png", 
        "Number of apps onboarded (weekly view)", 
        xtitle[0])
    pdf.image("./output/AppsOnboarded.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #-------------------------------------------------------------------------
    pdf.print_chapter('Number of scans per week',"")
    make_chart( 
        summary['timePeriodStart'], 
        summary['weeklyScans'], 
        "./output/WeeklyScans.png", 
        "Total number of scans per week", 
        xtitle[0])
    pdf.image("./output/WeeklyScans.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)

    #-------------------------------------------------------------------------
    header_most_scanned = ['Application','Total number of scans']
    data_most_scanned, aux = [],[]
    for app in apps:
        appName = app["applicationName"]
        scans = sum(app[report]["evaluationCount"]["rng"])
        aux = [appName,scans]
        data_most_scanned.append(aux)
    data_most_scanned.sort(key = lambda data_most_scanned: data_most_scanned[1], reverse = True)
    aux = []
    for i in range(0,len(data_most_scanned)):
        aux.append([data_most_scanned[i][0],str(data_most_scanned[i][1])])
    data_most_scanned = aux
    pdf.print_chapter('Most scanned applications','')
    pdf.fancy_table(header_most_scanned, data_most_scanned)
    t +=1
    printProgressBar(t,graphNo)

    #-------------------------------------------------------------------------
    
    if report == 'summary':
        pdf.print_chapter('Current open backlog (all violations)', "")
        content = "Number of open violations (backlog) per week (all violations)"
    elif report == 'security':
        pdf.print_chapter('Current open backlog (security violations only)', "")
        content = "Number of open violations (backlog) per week (security violations only)"
    elif report =='licences':
        pdf.print_chapter('Current open backlog (licensing violations only)', "")
        content = "Number of open violations (backlog) per week (licensing violations only)"
    make_stacked_chart(
        summary['timePeriodStart'],
        summary['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/OpenBacklog.png",
        content,
        xtitle[0],sonatype_colours)
    pdf.image("./output/OpenBacklog.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------

    if report == 'summary':
        pdf.print_chapter('Current risk per application sorted by criticality (all violations)', "")
    elif report == 'security':
        pdf.print_chapter('Current risk per application sorted by criticality (security violations only)', "")
    elif report =='licences':
        pdf.print_chapter('Current risk per application sorted by criticality (licensing violations only)', "")
    header_Open_App = ['Application', 'Critical','Severe','Moderate','Low']
    data_Open_App= []
    for app in apps:
        critical = app[report]['openCountsAtTimePeriodEnd'][selector]['CRITICAL']['rng'][-1]
        severe = app[report]['openCountsAtTimePeriodEnd'][selector]['SEVERE']['rng'][-1]
        moderate = app[report]['openCountsAtTimePeriodEnd'][selector]['MODERATE']['rng'][-1]
        low = app['summary']['openCountsAtTimePeriodEnd'][selector]['LOW']['rng'][-1]
        aux = [critical,severe,moderate,low]
        data_Open_App.append([app['applicationName']] + aux)
    data_Open_App.sort(key = lambda data_Open_App: data_Open_App[1], reverse = True)
    aux=[]
    for i in range(0,len(data_Open_App)):
        aux.append([data_Open_App[i][0],str(data_Open_App[i][1]),str(data_Open_App[i][2]),str(data_Open_App[i][3]),str(data_Open_App[i][4])])
    data_Open_App = aux
    pdf.fancy_table(header_Open_App, data_Open_App)
    t +=1
    printProgressBar(t,graphNo)

    
 #-------------------------------------------------------------------------
    if report == 'summary':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (all violations)', "")
    elif report == 'security':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (security violations)', "")
    elif report =='licences':
        pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (licensing violations)', "")
    if len(summary['timePeriodStart']) >= 4:
        header_riskRatio = ['Risk Ratio', summary['timePeriodStart'][-4], summary['timePeriodStart'][-3], summary['timePeriodStart'][-2], summary['timePeriodStart'][-1]]
        shift = [-4,-3,-2,-1]
    else:
        header_riskRatio = ['Risk Ratio']
        shift = []
        for k in range(0,len(summary['timePeriodStart'])):
            header_riskRatio.append(summary['timePeriodStart'][k - len(summary['timePeriodStart'])])
            shift.append(k - len(summary['timePeriodStart']))
    levels = ['Critical','Severe','Moderate','Low']
    measures = ['riskRatioCritical','riskRatioSevere','riskRatioModerate','riskRatioLow']
    data_riskRatio= []
    for i in range(0,len(levels)):
        data_riskRatio.append([levels[i]])
        for j in range(0, len(shift)):
            data_riskRatio[i].append(str(summary[measures[i]][shift[j]]))
    pdf.fancy_table(header_riskRatio, data_riskRatio)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    for app in apps:
        if report == 'summary':
            pdf.print_chapter('Report for Application: '+app["applicationName"]+ ' (all violations)','')
        elif report == 'security':
            pdf.print_chapter('Report for Application: '+app["applicationName"]+ ' (security violations)','')
        elif report =='licences':
            pdf.print_chapter('Report for Application: '+app["applicationName"]+ ' (licensing violations)','')
        if len(app['aggregations']) >= 4:
            header_evolution = ['Metric',app['aggregations'][-4]['timePeriodStart'],app['aggregations'][-3]['timePeriodStart'],app['aggregations'][-2]['timePeriodStart'],app['aggregations'][-1]['timePeriodStart']]
            shift = [-4,-3,-2,-1]
        else:
            header_evolution = ['Metric']
            shift = []
            for k in range(0,len(app['aggregations'])):
                header_evolution.append(app['aggregations'][k - len(app['aggregations'])]['timePeriodStart'])
                shift.append(k - len(app['aggregations']))
                
        metrics = ['MTTR Critical','MTTR Severe', 'MTTR Moderate','MTTR Low','Discovered Critical','Discovered Severe','Discovered Moderate','Discovered Low',
                   'Fixed Critical','Fixed Severe','Fixed Moderate','Fixed Low','Waived Critical','Waived Severe','Waived Moderate','Waived Low',
                   'Open Critical','Open Severe','Open Moderate','Open Low']
        measures = ['discoveredCounts','fixedCounts','waivedCounts','openCountsAtTimePeriodEnd']
        mttr = ['mttrCriticalThreat','mttrSevereThreat','mttrModerateThreat','mttrLowThreat']
        levels = ['CRITICAL','SEVERE','MODERATE','LOW']
        data_evolution = []

        for i in range(0,len(metrics)):
            data_evolution.append([metrics[i]])
            for j in range(0,len(shift)):
                if i <= 3:
                    data_evolution[i].append(str(app[report][mttr[i]]['rng'][shift[j]]))
                if 4 <= i <= 7:
                    data_evolution[i].append(str(app[report][measures[0]][selector][levels[i-4]]['rng'][shift[j]]))
                if 8 <= i <= 11:
                    data_evolution[i].append(str(app[report][measures[1]][selector][levels[i-8]]['rng'][shift[j]]))
                if 12 <= i <= 15:
                    data_evolution[i].append(str(app[report][measures[2]][selector][levels[i-12]]['rng'][shift[j]]))
                if 16 <= i <= 19:
                    data_evolution[i].append(str(app[report][measures[3]][selector][levels[i-16]]['rng'][shift[j]]))

        pdf.fancy_table(header_evolution,data_evolution)


        pdf.ln(10)
        
        header_last_week = ['Last week Open backlog','Critical','Severe','Moderate','Low']
        metrics = ['Discovered','Fixed','Waived','Open']
        measures = ['discoveredCounts','fixedCounts','waivedCounts','openCountsAtTimePeriodEnd']
        levels = ['CRITICAL','SEVERE','MODERATE','LOW']
                
        data_last_week = []

        for i in range(0,len(metrics)):
            data_last_week.append([metrics[i]])
            for j in levels:
                data_last_week[i].append(str(app[report][measures[i]][selector][j]['rng'][-1]))

        pdf.fancy_table(header_last_week,data_last_week)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    return pdf


#-------------------------------------------------------------------------


def main():
    
    for report in args:
        if args[report] == True:
            exec(report+"()")
           

if __name__ == "__main__":
    main()
#raise SystemExit

