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
import time
import plotly.graph_objects as go
import argparse

parser = argparse.ArgumentParser(description='get some reports')
parser.add_argument('-e','--executive', help='generates executive report for all violations', action='store_true', required=False)
parser.add_argument('-es','--executiveSec', help='generates executive report only for Security violations', action='store_true', required=False)
parser.add_argument('-el','--executiveLic', help='generates executive report only for Licensing violations', action='store_true', required=False)
parser.add_argument('-t','--tables', help='generates a report in table format for all violations', action='store_true', required=False)
parser.add_argument('-ts','--tablesSec', help='generates a report in table format only for Security violations', action='store_true', required=False)
parser.add_argument('-tl','--tablesLic', help='generates a report in table format only for Licensing violations', action='store_true', required=False)
parser.add_argument('-f','--file', help='input file', default='./output/successmetrics.json',dest='jsonFile', action='store', required=False)

args = vars(parser.parse_args())

xtitle = ["Date", "Applications", "Organisations"]
filename = args['jsonFile']
sonatype_colours = ['rgb(0,106,197)','rgb(253,198,22)','rgb(246,128,4)','rgb(205,0,40)']
disfixwai_colours = ['rgb(245,69,44)','rgb(0,209,146)','rgb(101,104,255)']


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

#EXECUTIVE: Executive summary report (combination of reports but without going into app level)
def executive():

    pages, t, graphNo = [], 0, 17
    appName, orgName, OpeLow, OpeMod, OpeSev, OpeCri, mttrLow, mttrMod, mttrSev, mttrCri = [],[],[],[],[],[],[],[],[],[]
    printProgressBar(t,graphNo)
    
    pdf = PDF()
    pdf.alias_nb_pages()

    ###########################
    header_Open_App = ['Application', 'Critical','Severe','Moderate','Low']
    data_Open_App= []
    for app in apps:
        critical = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['CRITICAL']['rng'][-1]
        severe = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['SEVERE']['rng'][-1]
        moderate = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['MODERATE']['rng'][-1]
        low = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['LOW']['rng'][-1]
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
    onboarded = summary["appOnboard"][-1]
    weeklyOnboard = average(onboarded,weeks,0,0)
    scanned = sum(summary["appNumberScan"])
    weeklyScanned = average(scanned,weeks,0,0)
    scans = sum(summary["weeklyScans"])
    weeklyScans = average(scans,weeks,0,0)
    discovered = sum(summary["discoveredCounts"]["TOTAL"])
    disCri = sum(summary["discoveredCounts"]["CRITICAL"])
    mostCri = data_Open_App[0][0]
    mostCriVal = data_Open_App[0][1]
    leastCri = data_Open_App[-1][0]
    leastCriVal = data_Open_App[-1][1]
    fixed = sum(summary["fixedCounts"]["TOTAL"])
    waived = sum(summary["waivedCounts"]["TOTAL"])
    dealt = fixed + waived
    dealtRate = round((dealt / discovered) * 100,1)
    riskRatio = [float(i) for i in summary["riskRatioCritical"]]
    riskRatioAvg = average(sum(riskRatio),weeks,0,0)
    mttrAvg = nonzeroAvg(summary["mttrCriticalThreat"],0,0)
    content1 = "In the past "+str(weeks)+" weeks your organisation:"
    content2 = "\t- Onboarded "+str(onboarded)+" applications at an average of "+str(weeklyOnboard)+" per week"
    content3 = "\t- Scanned applications "+str(scanned)+" times at an average of "+str(weeklyScanned)+" apps scanned per week"
    content4 = "\t- Performed "+str(scans)+" scans at an average of "+str(weeklyScans)+" scans per week"
    content5 = "\t- Discovered "+str(discovered)+" violations ("+str(disCri)+" of them Critical), fixing "+str(fixed)+" and waiving "+str(waived)+" of them"
    content6 = "\t  Which means that you have reduced "+str(dealtRate)+"% of your total risk"
    content7 = "\t- On average, each application had "+str(riskRatioAvg)+" Critical violations"
    content8 = "\t\t\t Most Criticals: "+str(mostCri)+" with "+str(mostCriVal)+" Critical violations"
    content9 = "\t\t\t Least Criticals: "+str(leastCri)+" with "+str(leastCriVal)+" Critical violations"
    content10 = "\t- It took an average of "+str(mttrAvg)+" days to fix Critical violations"
    pdf.print_chapter('Outcomes Summary (all violations)',"")
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
    pdf.ln(10)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(0,0,content6,0)
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0,0,content7,0)
    pdf.ln(10)
    pdf.cell(0,0,content8,0)
    pdf.ln(10)
    pdf.cell(0,0,content9,0)
    pdf.ln(15)
    pdf.cell(0,0,content10,0)


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
        scans = sum(app["summary"]["evaluationCount"]["rng"])
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
    pdf.print_chapter('Current open backlog for all violations', "")
    make_stacked_chart(
        summary['timePeriodStart'],
        summary['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/OpenBacklog.png",
        "Number of open violations (backlog) per week for all violations",
        xtitle[0],sonatype_colours)
    pdf.image("./output/OpenBacklog.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    #---------------------------------------------------------------------
    for app in apps:
        orgName.append(app["organizationName"])
        OpeLow.append(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["LOW"]["rng"][len(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["LOW"]["rng"])-1])
        OpeMod.append(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["MODERATE"]["rng"][len(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["MODERATE"]["rng"])-1])
        OpeSev.append(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["SEVERE"]["rng"][len(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["SEVERE"]["rng"])-1])
        OpeCri.append(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["CRITICAL"]["rng"][len(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["CRITICAL"]["rng"])-1])
    
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
       "Current Total Number of Open violations by organisation for all violations",
        xtitle[2],sonatype_colours
    )
    pdf.print_chapter('Current Total Number of Open violations by organisation for all violations', "")
    pdf.image("./output/Current_Open_Orgs.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    

    pdf.print_chapter('Current risk per application sorted by criticality for all violations (Top 100)',"")
    pdf.fancy_table(header_Open_App, data_Open_App)
    t +=1
    printProgressBar(t,graphNo)

#---------------------------------------------------------------------
    make_stacked_chart(
        summary['timePeriodStart'],
        [
            summary['discoveredCounts']['TOTAL'],
            summary['fixedCounts']['TOTAL'],
            summary['waivedCounts']['TOTAL']
        ],
       ['Discovered', 'Fixed', 'Waived'],
       "./output/Total_DisFixWaiCount.png", 
       "Total Number of Discovered, Fixed & Waived violations week-on-week",
        xtitle[0],disfixwai_colours
    )
    pdf.print_chapter('Total Number of Discovered, Fixed & Waived violations week-on-week (all violations)','')
    pdf.image("./output/Total_DisFixWaiCount.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['timePeriodStart'], 
        summary['discoveredCounts']['LIST'],
        ['Discovered Low', 'Discovered Moderate', 'Discovered Severe', 'Discovered Critical'],
        "./output/Discovered_breakdown.png",
        "Total Number of Discovered violations by severity week-on-week (all violations)",
        xtitle[0],sonatype_colours
    )
    pdf.print_chapter('Total Number of Discovered violations by severity week-on-week (all violations)','')
    pdf.image("./output/Discovered_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['timePeriodStart'], 
        summary['fixedCounts']['LIST'],
        ['Fixed Low', 'Fixed Moderate', 'Fixed Severe', 'Fixed Critical'],
        "./output/Fixed_breakdown.png",
        "Total Number of Fixed violations by severity week-on-week (all violations)",
        xtitle[0],sonatype_colours
    )
    pdf.print_chapter('Total Number of Fixed violations by severity week-on-week (all violations)','')
    pdf.image("./output/Fixed_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['timePeriodStart'], 
        summary['waivedCounts']['LIST'],
        ['Waived Low', 'Waived Moderate', 'Waived Severe', 'Waived Critical'],
        "./output/Waived_breakdown.png",
        "Total Number of Waived violations by severity week-on-week",
        xtitle[0],sonatype_colours
    )
    pdf.print_chapter('Total Number of Waived violations by severity week-on-week (all violations)','')
    pdf.image("./output/Waived_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
     #---------------------------------------------------------------------
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
     #---------------------------------------------------------------------
    make_chart( 
        summary['timePeriodStart'], 
        summary['mttrCriticalThreat'], 
        "./output/MTTR_Critical.png", 
        "MTTR (in days) for all Critical Threat violations week-on-week (all violations)", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Critical Threat violations week-on-week','')
    pdf.image('./output/MTTR_Critical.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
    #---------------------------------------------------------------------


    
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
    pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (all violations)',"")
    pdf.fancy_table(header_riskRatio, data_riskRatio)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------


    #-------------------------------------------------------------------------
    pdf.output('./output/executive_report.pdf', 'F')


#-------------------------------------------------------------------------

#---------------------------------
#EXECUTIVE SECURITY: Executive summary report only for Security violations (combination of reports but without going into app level)
def executiveSec():

    pages, t, graphNo = [], 0, 17
    appName, orgName, OpeLow, OpeMod, OpeSev, OpeCri, mttrLow, mttrMod, mttrSev, mttrCri = [],[],[],[],[],[],[],[],[],[]
    printProgressBar(t,graphNo)
    
    pdf = PDF()
    pdf.alias_nb_pages()

    ###########################
    header_Open_App = ['Application', 'Critical','Severe','Moderate','Low']
    data_Open_App= []
    for app in apps:
        critical = app['security']['openCountsAtTimePeriodEnd']['SECURITY']['CRITICAL']['rng'][-1]
        severe = app['security']['openCountsAtTimePeriodEnd']['SECURITY']['SEVERE']['rng'][-1]
        moderate = app['security']['openCountsAtTimePeriodEnd']['SECURITY']['MODERATE']['rng'][-1]
        low = app['security']['openCountsAtTimePeriodEnd']['SECURITY']['LOW']['rng'][-1]
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
    
    weeks = len(Security["weeks"])
    onboarded = Security["appOnboard"][-1]
    weeklyOnboard = average(onboarded,weeks,0,0)
    scanned = sum(Security["appNumberScan"])
    weeklyScanned = average(scanned,weeks,0,0)
    scans = sum(Security["weeklyScans"])
    weeklyScans = average(scans,weeks,0,0)
    discovered = sum(Security["discoveredCounts"]["TOTAL"])
    disCri = sum(Security["discoveredCounts"]["CRITICAL"])
    mostCri = data_Open_App[0][0]
    mostCriVal = data_Open_App[0][1]
    leastCri = data_Open_App[-1][0]
    leastCriVal = data_Open_App[-1][1]
    fixed = sum(Security["fixedCounts"]["TOTAL"])
    waived = sum(Security["waivedCounts"]["TOTAL"])
    dealt = fixed + waived
    dealtRate = round((dealt / discovered) * 100,1)
    riskRatio = [float(i) for i in Security["riskRatioCritical"]]
    riskRatioAvg = average(sum(riskRatio),weeks,0,0)
    mttrAvg = nonzeroAvg(Security["mttrCriticalThreat"],0,0)
    content1 = "In the past "+str(weeks)+" weeks your organisation:"
    content2 = "\t- Onboarded "+str(onboarded)+" applications at an average of "+str(weeklyOnboard)+" per week"
    content3 = "\t- Scanned applications "+str(scanned)+" times at an average of "+str(weeklyScanned)+" apps scanned per week"
    content4 = "\t- Performed "+str(scans)+" scans at an average of "+str(weeklyScans)+" scans per week"
    content5 = "\t- Discovered "+str(discovered)+" violations ("+str(disCri)+" of them Critical), fixing "+str(fixed)+" and waiving "+str(waived)+" of them"
    content6 = "\t  Which means that you have reduced "+str(dealtRate)+"% of your total risk"
    content7 = "\t- On average, each application had "+str(riskRatioAvg)+" Critical violations"
    content8 = "\t\t\t Most Criticals: "+str(mostCri)+" with "+str(mostCriVal)+" Critical violations"
    content9 = "\t\t\t Least Criticals: "+str(leastCri)+" with "+str(leastCriVal)+" Critical violations"
    content10 = "\t- It took an average of "+str(mttrAvg)+" days to fix Critical violations"
    pdf.print_chapter('Outcomes Summary (security violations)',"")
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
    pdf.ln(10)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(0,0,content6,0)
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0,0,content7,0)
    pdf.ln(10)
    pdf.cell(0,0,content8,0)
    pdf.ln(10)
    pdf.cell(0,0,content9,0)
    pdf.ln(15)
    pdf.cell(0,0,content10,0)


    t +=1
    printProgressBar(t,graphNo)

    ###########################

    
    #-------------------------------------------------------------------------
    pdf.print_chapter('Number of apps onboarded (weekly view)',"")
    make_chart( 
        Security['timePeriodStart'], 
        Security['appOnboard'], 
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
        Security['timePeriodStart'], 
        Security['appNumberScan'], 
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
        Security['timePeriodStart'], 
        Security['weeklyScans'], 
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
        scans = sum(app["security"]["evaluationCount"]["rng"])
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
    pdf.print_chapter('Current open backlog (security only)', "")
    make_stacked_chart(
        Security['timePeriodStart'],
        Security['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/OpenBacklog.png",
        "Number of open violations (backlog) per week (security only)",
        xtitle[0],sonatype_colours)
    pdf.image("./output/OpenBacklog.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    #---------------------------------------------------------------------
    for app in apps:
        orgName.append(app["organizationName"])
        OpeLow.append(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["LOW"]["rng"][len(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["LOW"]["rng"])-1])
        OpeMod.append(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["MODERATE"]["rng"][len(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["MODERATE"]["rng"])-1])
        OpeSev.append(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["SEVERE"]["rng"][len(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["SEVERE"]["rng"])-1])
        OpeCri.append(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["CRITICAL"]["rng"][len(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["CRITICAL"]["rng"])-1])
    
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
       "Current Total Number of Open violations by organisation (security only)",
        xtitle[2],sonatype_colours
    )
    pdf.print_chapter('Current Total Number of Open violations by organisation (security only)', "")
    pdf.image("./output/Current_Open_Orgs.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    

    pdf.print_chapter('Current risk per application sorted by criticality (Top 100) (security only)',"")
    pdf.fancy_table(header_Open_App, data_Open_App)
    t +=1
    printProgressBar(t,graphNo)

#---------------------------------------------------------------------
    make_stacked_chart(
        Security['timePeriodStart'],
        [
            Security['discoveredCounts']['TOTAL'],
            Security['fixedCounts']['TOTAL'],
            Security['waivedCounts']['TOTAL']
        ],
       ['Discovered', 'Fixed', 'Waived'],
       "./output/Total_DisFixWaiCount.png", 
       "Total Number of Discovered, Fixed & Waived violations week-on-week (security only)",
        xtitle[0],disfixwai_colours
    )
    pdf.print_chapter('Total Number of Discovered, Fixed & Waived violations week-on-week (security only)','')
    pdf.image("./output/Total_DisFixWaiCount.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        Security['timePeriodStart'], 
        Security['discoveredCounts']['LIST'],
        ['Discovered Low', 'Discovered Moderate', 'Discovered Severe', 'Discovered Critical'],
        "./output/Discovered_breakdown.png",
        "Total Number of Discovered violations by severity week-on-week (security only)",
        xtitle[0],sonatype_colours
    )
    pdf.print_chapter('Total Number of Discovered violations by severity week-on-week (security only)','')
    pdf.image("./output/Discovered_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        Security['timePeriodStart'], 
        Security['fixedCounts']['LIST'],
        ['Fixed Low', 'Fixed Moderate', 'Fixed Severe', 'Fixed Critical'],
        "./output/Fixed_breakdown.png",
        "Total Number of Fixed violations by severity week-on-week (security only)",
        xtitle[0],sonatype_colours
    )
    pdf.print_chapter('Total Number of Fixed violations by severity week-on-week (security only)','')
    pdf.image("./output/Fixed_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        Security['timePeriodStart'], 
        Security['waivedCounts']['LIST'],
        ['Waived Low', 'Waived Moderate', 'Waived Severe', 'Waived Critical'],
        "./output/Waived_breakdown.png",
        "Total Number of Waived violations by severity week-on-week (security only)",
        xtitle[0],sonatype_colours
    )
    pdf.print_chapter('Total Number of Waived violations by severity week-on-week (security only)','')
    pdf.image("./output/Waived_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        Security['timePeriodStart'], 
        Security['mttrLowThreat'], 
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
        Security['timePeriodStart'], 
        Security['mttrModerateThreat'], 
        "./output/MTTR_Moderate.png", 
        "MTTR (in days) for all Moderate Threat violations week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Moderate Threat violations week-on-week','')
    pdf.image('./output/MTTR_Moderate.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        Security['timePeriodStart'], 
        Security['mttrSevereThreat'], 
        "./output/MTTR_Severe.png", 
        "MTTR (in days) for all Severe Threat violations week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Severe Threat violations week-on-week','')
    pdf.image('./output/MTTR_Severe.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        Security['timePeriodStart'], 
        Security['mttrCriticalThreat'], 
        "./output/MTTR_Critical.png", 
        "MTTR (in days) for all Critical Threat violations week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Critical Threat violations week-on-week','')
    pdf.image('./output/MTTR_Critical.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
    #---------------------------------------------------------------------


    
 #-------------------------------------------------------------------------
    if len(Security['timePeriodStart']) >= 4:
        header_riskRatio = ['Risk Ratio', Security['timePeriodStart'][-4], Security['timePeriodStart'][-3], Security['timePeriodStart'][-2], Security['timePeriodStart'][-1]]
        shift = [-4,-3,-2,-1]
    else:
        header_riskRatio = ['Risk Ratio']
        shift = []
        for k in range(0,len(Security['timePeriodStart'])):
            header_riskRatio.append(Security['timePeriodStart'][k - len(Security['timePeriodStart'])])
            shift.append(k - len(Security['timePeriodStart']))
    levels = ['Critical','Severe','Moderate','Low']
    measures = ['riskRatioCritical','riskRatioSevere','riskRatioModerate','riskRatioLow']
    data_riskRatio= []
    for i in range(0,len(levels)):
        data_riskRatio.append([levels[i]])
        for j in range(0, len(shift)):
            data_riskRatio[i].append(str(Security[measures[i]][shift[j]]))
    pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (security only)',"")
    pdf.fancy_table(header_riskRatio, data_riskRatio)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    
    #-------------------------------------------------------------------------
    pdf.output('./output/executive_security_report.pdf', 'F')


#-------------------------------------------------------------------------

#---------------------------------
#EXECUTIVE LICENSING: Executive summary report only for Licensing violations (combination of reports but without going into app level)
def executiveLic():

    pages, t, graphNo = [], 0, 17
    appName, orgName, OpeLow, OpeMod, OpeSev, OpeCri, mttrLow, mttrMod, mttrSev, mttrCri = [],[],[],[],[],[],[],[],[],[]
    printProgressBar(t,graphNo)
    
    pdf = PDF()
    pdf.alias_nb_pages()

###########################
    header_Open_App = ['Application', 'Critical','Severe','Moderate','Low']
    data_Open_App= []
    for app in apps:
        critical = app['licences']['openCountsAtTimePeriodEnd']['LICENSE']['CRITICAL']['rng'][-1]
        severe = app['licences']['openCountsAtTimePeriodEnd']['LICENSE']['SEVERE']['rng'][-1]
        moderate = app['licences']['openCountsAtTimePeriodEnd']['LICENSE']['MODERATE']['rng'][-1]
        low = app['licences']['openCountsAtTimePeriodEnd']['LICENSE']['LOW']['rng'][-1]
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
    
    weeks = len(licences["weeks"])
    onboarded = licences["appOnboard"][-1]
    weeklyOnboard = average(onboarded,weeks,0,0)
    scanned = sum(licences["appNumberScan"])
    weeklyScanned = average(scanned,weeks,0,0)
    scans = sum(licences["weeklyScans"])
    weeklyScans = average(scans,weeks,0,0)
    discovered = sum(licences["discoveredCounts"]["TOTAL"])
    disCri = sum(licences["discoveredCounts"]["CRITICAL"])
    mostCri = data_Open_App[0][0]
    mostCriVal = data_Open_App[0][1]
    leastCri = data_Open_App[-1][0]
    leastCriVal = data_Open_App[-1][1]
    fixed = sum(licences["fixedCounts"]["TOTAL"])
    waived = sum(licences["waivedCounts"]["TOTAL"])
    dealt = fixed + waived
    dealtRate = round((dealt / discovered) * 100,1)
    riskRatio = [float(i) for i in licences["riskRatioCritical"]]
    riskRatioAvg = average(sum(riskRatio),weeks,0,0)
    mttrAvg = nonzeroAvg(licences["mttrCriticalThreat"],0,0)
    content1 = "In the past "+str(weeks)+" weeks your organisation:"
    content2 = "\t- Onboarded "+str(onboarded)+" applications at an average of "+str(weeklyOnboard)+" per week"
    content3 = "\t- Scanned applications "+str(scanned)+" times at an average of "+str(weeklyScanned)+" apps scanned per week"
    content4 = "\t- Performed "+str(scans)+" scans at an average of "+str(weeklyScans)+" scans per week"
    content5 = "\t- Discovered "+str(discovered)+" violations ("+str(disCri)+" of them Critical), fixing "+str(fixed)+" and waiving "+str(waived)+" of them"
    content6 = "\t  Which means that you have reduced "+str(dealtRate)+"% of your total risk"
    content7 = "\t- On average, each application had "+str(riskRatioAvg)+" Critical violations"
    content8 = "\t\t\t Most Criticals: "+str(mostCri)+" with "+str(mostCriVal)+" Critical violations"
    content9 = "\t\t\t Least Criticals: "+str(leastCri)+" with "+str(leastCriVal)+" Critical violations"
    content10 = "\t- It took an average of "+str(mttrAvg)+" days to fix Critical violations"
    pdf.print_chapter('Outcomes Summary (licensing violations)',"")
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
    pdf.ln(10)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(0,0,content6,0)
    pdf.ln(15)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0,0,content7,0)
    pdf.ln(10)
    pdf.cell(0,0,content8,0)
    pdf.ln(10)
    pdf.cell(0,0,content9,0)
    pdf.ln(15)
    pdf.cell(0,0,content10,0)


    t +=1
    printProgressBar(t,graphNo)

    ###########################


    
    #-------------------------------------------------------------------------
    pdf.print_chapter('Number of apps onboarded (weekly view)',"")
    make_chart( 
        licences['timePeriodStart'], 
        licences['appOnboard'], 
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
        licences['timePeriodStart'], 
        licences['appNumberScan'], 
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
        licences['timePeriodStart'], 
        licences['weeklyScans'], 
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
        scans = sum(app["licences"]["evaluationCount"]["rng"])
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
    pdf.print_chapter('Current open backlog (licensing only)', "")
    make_stacked_chart(
        licences['timePeriodStart'],
        licences['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/OpenBacklog.png",
        "Number of open violations (backlog) per week (licensing only)",
        xtitle[0],sonatype_colours)
    pdf.image("./output/OpenBacklog.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    #---------------------------------------------------------------------
    for app in apps:
        orgName.append(app["organizationName"])
        OpeLow.append(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["LOW"]["rng"][len(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["LOW"]["rng"])-1])
        OpeMod.append(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["MODERATE"]["rng"][len(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["MODERATE"]["rng"])-1])
        OpeSev.append(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["SEVERE"]["rng"][len(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["SEVERE"]["rng"])-1])
        OpeCri.append(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["CRITICAL"]["rng"][len(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["CRITICAL"]["rng"])-1])
    
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
       "Current Total Number of Open violations by organisation (licensing only)",
        xtitle[2],sonatype_colours
    )
    pdf.print_chapter('Current Total Number of Open violations by organisation (licensing only)', "")
    pdf.image("./output/Current_Open_Orgs.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    
    pdf.print_chapter('Current risk per application sorted by criticality (Top 100) (licensing only)',"")
    pdf.fancy_table(header_Open_App, data_Open_App)
    t +=1
    printProgressBar(t,graphNo)

#---------------------------------------------------------------------
    make_stacked_chart(
        licences['timePeriodStart'],
        [
            licences['discoveredCounts']['TOTAL'],
            licences['fixedCounts']['TOTAL'],
            licences['waivedCounts']['TOTAL']
        ],
       ['Discovered', 'Fixed', 'Waived'],
       "./output/Total_DisFixWaiCount.png", 
       "Total Number of Discovered, Fixed & Waived violations week-on-week (licensing only)",
        xtitle[0],disfixwai_colours
    )
    pdf.print_chapter('Total Number of Discovered, Fixed & Waived violations week-on-week (licensing only)','')
    pdf.image("./output/Total_DisFixWaiCount.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        licences['timePeriodStart'], 
        licences['discoveredCounts']['LIST'],
        ['Discovered Low', 'Discovered Moderate', 'Discovered Severe', 'Discovered Critical'],
        "./output/Discovered_breakdown.png",
        "Total Number of Discovered violations by severity week-on-week (licensing only)",
        xtitle[0],sonatype_colours
    )
    pdf.print_chapter('Total Number of Discovered violations by severity week-on-week (licensing only)','')
    pdf.image("./output/Discovered_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        licences['timePeriodStart'], 
        licences['fixedCounts']['LIST'],
        ['Fixed Low', 'Fixed Moderate', 'Fixed Severe', 'Fixed Critical'],
        "./output/Fixed_breakdown.png",
        "Total Number of Fixed violations by severity week-on-week (licensing only)",
        xtitle[0],sonatype_colours
    )
    pdf.print_chapter('Total Number of Fixed violations by severity week-on-week (licensing only)','')
    pdf.image("./output/Fixed_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        licences['timePeriodStart'], 
        licences['waivedCounts']['LIST'],
        ['Waived Low', 'Waived Moderate', 'Waived Severe', 'Waived Critical'],
        "./output/Waived_breakdown.png",
        "Total Number of Waived violations by severity week-on-week (licensing only)",
        xtitle[0],sonatype_colours
    )
    pdf.print_chapter('Total Number of Waived violations by severity week-on-week (licensing only)','')
    pdf.image("./output/Waived_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        licences['timePeriodStart'], 
        licences['mttrLowThreat'], 
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
        licences['timePeriodStart'], 
        licences['mttrModerateThreat'], 
        "./output/MTTR_Moderate.png", 
        "MTTR (in days) for all Moderate Threat violations week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Moderate Threat violations week-on-week','')
    pdf.image('./output/MTTR_Moderate.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        licences['timePeriodStart'], 
        licences['mttrSevereThreat'], 
        "./output/MTTR_Severe.png", 
        "MTTR (in days) for all Severe Threat violations week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Severe Threat violations week-on-week','')
    pdf.image('./output/MTTR_Severe.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        licences['timePeriodStart'], 
        licences['mttrCriticalThreat'], 
        "./output/MTTR_Critical.png", 
        "MTTR (in days) for all Critical Threat violations week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Critical Threat violations week-on-week','')
    pdf.image('./output/MTTR_Critical.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
    #---------------------------------------------------------------------


    
 #-------------------------------------------------------------------------
    if len(licences['timePeriodStart']) >= 4:
        header_riskRatio = ['Risk Ratio', licences['timePeriodStart'][-4], licences['timePeriodStart'][-3], licences['timePeriodStart'][-2], licences['timePeriodStart'][-1]]
        shift = [-4,-3,-2,-1]
    else:
        header_riskRatio = ['Risk Ratio']
        shift = []
        for k in range(0,len(licences['timePeriodStart'])):
            header_riskRatio.append(licences['timePeriodStart'][k - len(licences['timePeriodStart'])])
            shift.append(k - len(licences['timePeriodStart']))
    levels = ['Critical','Severe','Moderate','Low']
    measures = ['riskRatioCritical','riskRatioSevere','riskRatioModerate','riskRatioLow']
    data_riskRatio= []
    for i in range(0,len(levels)):
        data_riskRatio.append([levels[i]])
        for j in range(0, len(shift)):
            data_riskRatio[i].append(str(licences[measures[i]][shift[j]]))
    pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (licensing only)',"")
    pdf.fancy_table(header_riskRatio, data_riskRatio)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    
    #-------------------------------------------------------------------------
    pdf.output('./output/executive_licensing_report.pdf', 'F')


#-------------------------------------------------------------------------




#-------------------------------------------------------------------------
#TABLES: "To provide a report for all violations, in table format to accommodate for customers with thousands of applications"
#-------------------------------------------------------------------------
    
# Instantiation of inherited class
def tables():
    pages, t, graphNo = [], 0, 7
    printProgressBar(t,graphNo)
    
    pdf = PDF()
    pdf.alias_nb_pages()
    
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
        scans = sum(app["summary"]["evaluationCount"]["rng"])
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
    pdf.print_chapter('Current open backlog (all violations)', "")
    make_stacked_chart(
        summary['timePeriodStart'],
        summary['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/OpenBacklog.png",
        "Number of open violations (backlog) per week (all violations)",
        xtitle[0],sonatype_colours)
    pdf.image("./output/OpenBacklog.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    header_Open_App = ['Application', 'Critical','Severe','Moderate','Low']
    data_Open_App= []
    for app in apps:
        critical = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['CRITICAL']['rng'][-1]
        severe = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['SEVERE']['rng'][-1]
        moderate = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['MODERATE']['rng'][-1]
        low = app['summary']['openCountsAtTimePeriodEnd']['TOTAL']['LOW']['rng'][-1]
        aux = [critical,severe,moderate,low]
        data_Open_App.append([app['applicationName']] + aux)
    data_Open_App.sort(key = lambda data_Open_App: data_Open_App[1], reverse = True)
    aux=[]
    for i in range(0,len(data_Open_App)):
        aux.append([data_Open_App[i][0],str(data_Open_App[i][1]),str(data_Open_App[i][2]),str(data_Open_App[i][3]),str(data_Open_App[i][4])])
    data_Open_App = aux
    pdf.print_chapter('Current risk per application sorted by criticality (all violations)',"")
    pdf.fancy_table(header_Open_App, data_Open_App)
    t +=1
    printProgressBar(t,graphNo)

    
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
    pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (all violations)',"")
    pdf.fancy_table(header_riskRatio, data_riskRatio)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    for app in apps:
        pdf.print_chapter('Report for Application: '+app["applicationName"]+ ' (all violations)','')
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
                    data_evolution[i].append(str(app['summary'][mttr[i]]['rng'][shift[j]]))
                if 4 <= i <= 7:
                    data_evolution[i].append(str(app['summary'][measures[0]]['TOTAL'][levels[i-4]]['rng'][shift[j]]))
                if 8 <= i <= 11:
                    data_evolution[i].append(str(app['summary'][measures[1]]['TOTAL'][levels[i-8]]['rng'][shift[j]]))
                if 12 <= i <= 15:
                    data_evolution[i].append(str(app['summary'][measures[2]]['TOTAL'][levels[i-12]]['rng'][shift[j]]))
                if 16 <= i <= 19:
                    data_evolution[i].append(str(app['summary'][measures[3]]['TOTAL'][levels[i-16]]['rng'][shift[j]]))

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
                data_last_week[i].append(str(app['summary'][measures[i]]['TOTAL'][j]['rng'][-1]))

        pdf.fancy_table(header_last_week,data_last_week)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    pdf.output('./output/tables_report.pdf', 'F')


#-------------------------------------------------------------------------
#TABLES SECURITY: "To provide a report for Security violations only, in table format to accommodate for customers with thousands of applications"
#-------------------------------------------------------------------------
    
# Instantiation of inherited class
def tablesSec():
    pages, t, graphNo = [], 0, 7
    printProgressBar(t,graphNo)
    
    pdf = PDF()
    pdf.alias_nb_pages()
    
    #-------------------------------------------------------------------------
    pdf.print_chapter('Number of apps onboarded (weekly view)',"")
    make_chart( 
        Security['timePeriodStart'], 
        Security['appOnboard'], 
        "./output/AppsOnboarded.png", 
        "Number of apps onboarded (weekly view)", 
        xtitle[0])
    pdf.image("./output/AppsOnboarded.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #-------------------------------------------------------------------------
    pdf.print_chapter('Number of scans per week',"")
    make_chart( 
        Security['timePeriodStart'], 
        Security['weeklyScans'], 
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
        scans = sum(app["security"]["evaluationCount"]["rng"])
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
    pdf.print_chapter('Current open backlog (security only)', "")
    make_stacked_chart(
        Security['timePeriodStart'],
        Security['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/OpenBacklog.png",
        "Number of open violations (backlog) per week (security only)",
        xtitle[0],sonatype_colours)
    pdf.image("./output/OpenBacklog.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    header_Open_App = ['Application', 'Critical','Severe','Moderate','Low']
    data_Open_App= []
    for app in apps:
        critical = app['security']['openCountsAtTimePeriodEnd']['TOTAL']['CRITICAL']['rng'][-1]
        severe = app['security']['openCountsAtTimePeriodEnd']['TOTAL']['SEVERE']['rng'][-1]
        moderate = app['security']['openCountsAtTimePeriodEnd']['TOTAL']['MODERATE']['rng'][-1]
        low = app['security']['openCountsAtTimePeriodEnd']['TOTAL']['LOW']['rng'][-1]
        aux = [critical,severe,moderate,low]
        data_Open_App.append([app['applicationName']] + aux)
    data_Open_App.sort(key = lambda data_Open_App: data_Open_App[1], reverse = True)
    aux=[]
    for i in range(0,len(data_Open_App)):
        aux.append([data_Open_App[i][0],str(data_Open_App[i][1]),str(data_Open_App[i][2]),str(data_Open_App[i][3]),str(data_Open_App[i][4])])
    data_Open_App = aux
    pdf.print_chapter('Current risk per application sorted by criticality (security only)',"")
    pdf.fancy_table(header_Open_App, data_Open_App)
    t +=1
    printProgressBar(t,graphNo)

    
 #-------------------------------------------------------------------------
    if len(Security['timePeriodStart']) >= 4:
        header_riskRatio = ['Risk Ratio', Security['timePeriodStart'][-4], Security['timePeriodStart'][-3], Security['timePeriodStart'][-2], Security['timePeriodStart'][-1]]
        shift = [-4,-3,-2,-1]
    else:
        header_riskRatio = ['Risk Ratio']
        shift = []
        for k in range(0,len(Security['timePeriodStart'])):
            header_riskRatio.append(Security['timePeriodStart'][k - len(Security['timePeriodStart'])])
            shift.append(k - len(Security['timePeriodStart']))
    levels = ['Critical','Severe','Moderate','Low']
    measures = ['riskRatioCritical','riskRatioSevere','riskRatioModerate','riskRatioLow']
    data_riskRatio= []
    for i in range(0,len(levels)):
        data_riskRatio.append([levels[i]])
        for j in range(0, len(shift)):
            data_riskRatio[i].append(str(Security[measures[i]][shift[j]]))
    pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (security only)',"")
    pdf.fancy_table(header_riskRatio, data_riskRatio)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    for app in apps:
        pdf.print_chapter('Report for Application: '+app["applicationName"]+' (security only)','')
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
                    data_evolution[i].append(str(app['security'][mttr[i]]['rng'][shift[j]]))
                if 4 <= i <= 7:
                    data_evolution[i].append(str(app['security'][measures[0]]['TOTAL'][levels[i-4]]['rng'][shift[j]]))
                if 8 <= i <= 11:
                    data_evolution[i].append(str(app['security'][measures[1]]['TOTAL'][levels[i-8]]['rng'][shift[j]]))
                if 12 <= i <= 15:
                    data_evolution[i].append(str(app['security'][measures[2]]['TOTAL'][levels[i-12]]['rng'][shift[j]]))
                if 16 <= i <= 19:
                    data_evolution[i].append(str(app['security'][measures[3]]['TOTAL'][levels[i-16]]['rng'][shift[j]]))

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
                data_last_week[i].append(str(app['security'][measures[i]]['TOTAL'][j]['rng'][-1]))

        pdf.fancy_table(header_last_week,data_last_week)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    pdf.output('./output/tables_security_report.pdf', 'F')


#-------------------------------------------------------------------------
#TABLES LICENSING: "To provide a report for licensing violations only, in table format to accommodate for customers with thousands of applications"
#-------------------------------------------------------------------------
    
# Instantiation of inherited class
def tablesLic():
    pages, t, graphNo = [], 0, 7
    printProgressBar(t,graphNo)
    
    pdf = PDF()
    pdf.alias_nb_pages()
    
    #-------------------------------------------------------------------------
    pdf.print_chapter('Number of apps onboarded (weekly view)',"")
    make_chart( 
        licences['timePeriodStart'], 
        licences['appOnboard'], 
        "./output/AppsOnboarded.png", 
        "Number of apps onboarded (weekly view)", 
        xtitle[0])
    pdf.image("./output/AppsOnboarded.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #-------------------------------------------------------------------------
    pdf.print_chapter('Number of scans per week',"")
    make_chart( 
        licences['timePeriodStart'], 
        licences['weeklyScans'], 
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
        scans = sum(app["licences"]["evaluationCount"]["rng"])
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
    pdf.print_chapter('Current open backlog (licensing only)', "")
    make_stacked_chart(
        licences['timePeriodStart'],
        licences['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/OpenBacklog.png",
        "Number of open violations (backlog) per week (licensing only)",
        xtitle[0],sonatype_colours)
    pdf.image("./output/OpenBacklog.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    header_Open_App = ['Application', 'Critical','Severe','Moderate','Low']
    data_Open_App= []
    for app in apps:
        critical = app['licences']['openCountsAtTimePeriodEnd']['TOTAL']['CRITICAL']['rng'][-1]
        severe = app['licences']['openCountsAtTimePeriodEnd']['TOTAL']['SEVERE']['rng'][-1]
        moderate = app['licences']['openCountsAtTimePeriodEnd']['TOTAL']['MODERATE']['rng'][-1]
        low = app['licences']['openCountsAtTimePeriodEnd']['TOTAL']['LOW']['rng'][-1]
        aux = [critical,severe,moderate,low]
        data_Open_App.append([app['applicationName']] + aux)
    data_Open_App.sort(key = lambda data_Open_App: data_Open_App[1], reverse = True)
    aux=[]
    for i in range(0,len(data_Open_App)):
        aux.append([data_Open_App[i][0],str(data_Open_App[i][1]),str(data_Open_App[i][2]),str(data_Open_App[i][3]),str(data_Open_App[i][4])])
    data_Open_App = aux
    pdf.print_chapter('Current risk per application sorted by criticality (licensing only)',"")
    pdf.fancy_table(header_Open_App, data_Open_App)
    t +=1
    printProgressBar(t,graphNo)

    
 #-------------------------------------------------------------------------
    if len(licences['timePeriodStart']) >= 4:
        header_riskRatio = ['Risk Ratio', licences['timePeriodStart'][-4], licences['timePeriodStart'][-3], licences['timePeriodStart'][-2], licences['timePeriodStart'][-1]]
        shift = [-4,-3,-2,-1]
    else:
        header_riskRatio = ['Risk Ratio']
        shift = []
        for k in range(0,len(licences['timePeriodStart'])):
            header_riskRatio.append(licences['timePeriodStart'][k - len(licences['timePeriodStart'])])
            shift.append(k - len(licences['timePeriodStart']))
    levels = ['Critical','Severe','Moderate','Low']
    measures = ['riskRatioCritical','riskRatioSevere','riskRatioModerate','riskRatioLow']
    data_riskRatio= []
    for i in range(0,len(levels)):
        data_riskRatio.append([levels[i]])
        for j in range(0, len(shift)):
            data_riskRatio[i].append(str(licences[measures[i]][shift[j]]))
    pdf.print_chapter('Risk Ratio (number of violations / apps onboarded) by severity (licensing only)',"")
    pdf.fancy_table(header_riskRatio, data_riskRatio)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    for app in apps:
        pdf.print_chapter('Report for Application: '+app["applicationName"]+' (licensing only)','')
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
                    data_evolution[i].append(str(app['licences'][mttr[i]]['rng'][shift[j]]))
                if 4 <= i <= 7:
                    data_evolution[i].append(str(app['licences'][measures[0]]['TOTAL'][levels[i-4]]['rng'][shift[j]]))
                if 8 <= i <= 11:
                    data_evolution[i].append(str(app['licences'][measures[1]]['TOTAL'][levels[i-8]]['rng'][shift[j]]))
                if 12 <= i <= 15:
                    data_evolution[i].append(str(app['licences'][measures[2]]['TOTAL'][levels[i-12]]['rng'][shift[j]]))
                if 16 <= i <= 19:
                    data_evolution[i].append(str(app['licences'][measures[3]]['TOTAL'][levels[i-16]]['rng'][shift[j]]))

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
                data_last_week[i].append(str(app['licences'][measures[i]]['TOTAL'][j]['rng'][-1]))

        pdf.fancy_table(header_last_week,data_last_week)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    pdf.output('./output/tables_licensing_report.pdf', 'F')


#-------------------------------------------------------------------------


def main():
    
    for report in args:
        if args[report] == True:
            exec(report+"()")
           

if __name__ == "__main__":
    main()
#raise SystemExit

