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
parser.add_argument('-e','--executive', help='generates executive report', action='store_true', required=False)
parser.add_argument('-t','--tables', help='generates a report in table format', action='store_true', required=False)
parser.add_argument('-f','--file', help='input file', dest='jsonFile', action='store', required=False)

args = vars(parser.parse_args())

xtitle = ["Date", "Applications", "Organisations"]
filename = args['jsonFile']

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
        data=[ go.Bar(x=period, y=data, text=data, textposition='auto') ], 
        layout_title_text=title
    )

    fig.update_layout(autosize=False, width=864, height=528, xaxis=go.layout.XAxis(title_text=xtitle))
    fig.update_xaxes(tickvals=period,automargin=True)

    fig.write_image(filename)

def make_stacked_chart(period, data, legend, filename, title, xtitle):
    traces = []
    for i in range(0, len(data)):
        trace = go.Bar(
            name = legend[i],
            x = period,
            y = data[i],
            text = data[i],
            textposition = 'auto'
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
#ADOPTION: "To increase the use of Nexus IQ within my organisation".
#Tracks total number of applications onboarded (weekly basis)
#Tracks number of applications scanned per week (per org)
#Generates scans/week (total, per org, per app). 
#Tracks compliance percentage of minimum of x scans per week on all apps
#Generates discovered, fixed & waived counts/week (total, per org, per app).
#Tracks compliance percentage of fix, waive & dealt-with percentage per week and threat level
#Generates open counts/week (total, per org, per app). 
#Displays current technical debt, and tracks how long (in hours) 
#would it take to deal with it at current dealt-with rate (for informational purposes).

#---------------------------------
#EXECUTIVE: Executive summary report (combination of reports but without going into app level)
def executive():

    pages, t, graphNo = [], 0, 16
    appName, orgName, OpeLow, OpeMod, OpeSev, OpeCri, mttrLow, mttrMod, mttrSev, mttrCri = [],[],[],[],[],[],[],[],[],[]
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
    for i in range(0,len(data_most_scanned)):
        aux.append([data_most_scanned[i][0],str(data_most_scanned[i][1])])
    data_most_scanned = aux
    pdf.print_chapter('Most scanned applications','')
    pdf.fancy_table(header_most_scanned, data_most_scanned)
    t +=1
    printProgressBar(t,graphNo)

    #-------------------------------------------------------------------------
    pdf.print_chapter('Current open backlog', "")
    make_stacked_chart(
        summary['timePeriodStart'],
        summary['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/OpenBacklog.png",
        "Number of open vulnerabilities (backlog) per week",
        xtitle[0])
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
       "Current Total Number of Open vulnerabilities by organisation",
        xtitle[2]
    )
    pdf.print_chapter('Current Total Number of Open vulnerabilities by organisation', "")
    pdf.image("./output/Current_Open_Orgs.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    
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
    pdf.print_chapter('Current risk per application sorted by criticality',"")
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
       "Total Number of Discovered, Fixed & Waived vulnerabilities week-on-week",
        xtitle[0]
    )
    pdf.print_chapter('Total Number of Discovered, Fixed & Waived vulnerabilities week-on-week','')
    pdf.image("./output/Total_DisFixWaiCount.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['timePeriodStart'], 
        summary['discoveredCounts']['LIST'],
        ['Discovered Low', 'Discovered Moderate', 'Discovered Severe', 'Discovered Critical'],
        "./output/Discovered_breakdown.png",
        "Total Number of Discovered vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pdf.print_chapter('Total Number of Discovered vulnerabilities by severity week-on-week','')
    pdf.image("./output/Discovered_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['timePeriodStart'], 
        summary['fixedCounts']['LIST'],
        ['Fixed Low', 'Fixed Moderate', 'Fixed Severe', 'Fixed Critical'],
        "./output/Fixed_breakdown.png",
        "Total Number of Fixed vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pdf.print_chapter('Total Number of Fixed vulnerabilities by severity week-on-week','')
    pdf.image("./output/Fixed_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['timePeriodStart'], 
        summary['waivedCounts']['LIST'],
        ['Waived Low', 'Waived Moderate', 'Waived Severe', 'Waived Critical'],
        "./output/Waived_breakdown.png",
        "Total Number of Waived vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pdf.print_chapter('Total Number of Waived vulnerabilities by severity week-on-week','')
    pdf.image("./output/Waived_breakdown.png",10,36,270)
    t +=1
    printProgressBar(t,graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        summary['timePeriodStart'], 
        summary['mttrLowThreat'], 
        "./output/MTTR_Low.png", 
        "MTTR (in days) for all Low Threat vulnerabilities week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Low Threat vulnerabilities week-on-week','')
    pdf.image('./output/MTTR_Low.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        summary['timePeriodStart'], 
        summary['mttrModerateThreat'], 
        "./output/MTTR_Moderate.png", 
        "MTTR (in days) for all Moderate Threat vulnerabilities week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Moderate Threat vulnerabilities week-on-week','')
    pdf.image('./output/MTTR_Moderate.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        summary['timePeriodStart'], 
        summary['mttrSevereThreat'], 
        "./output/MTTR_Severe.png", 
        "MTTR (in days) for all Severe Threat vulnerabilities week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Severe Threat vulnerabilities week-on-week','')
    pdf.image('./output/MTTR_Severe.png',10,36,270)
    t +=1
    printProgressBar(t, graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        summary['timePeriodStart'], 
        summary['mttrCriticalThreat'], 
        "./output/MTTR_Critical.png", 
        "MTTR (in days) for all Critical Threat vulnerabilities week-on-week", 
        xtitle[0]
    )
    pdf.print_chapter('MTTR (in days) for all Critical Threat vulnerabilities week-on-week','')
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
    pdf.print_chapter('Risk Ratio (number of vulnerabilities / apps onboarded) by severity',"")
    pdf.fancy_table(header_riskRatio, data_riskRatio)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    
    #-------------------------------------------------------------------------
    pdf.output('./output/executive_report.pdf', 'F')


#-------------------------------------------------------------------------


#-------------------------------------------------------------------------
#TABLES: "To provide a report in table format to accommodate for customers with thousands of applications"
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
    pdf.print_chapter('Current open backlog', "")
    make_stacked_chart(
        summary['timePeriodStart'],
        summary['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/OpenBacklog.png",
        "Number of open vulnerabilities (backlog) per week",
        xtitle[0])
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
    pdf.print_chapter('Current risk per application sorted by criticality',"")
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
    pdf.print_chapter('Risk Ratio (number of vulnerabilities / apps onboarded) by severity',"")
    pdf.fancy_table(header_riskRatio, data_riskRatio)
    t +=1
    printProgressBar(t,graphNo)
    
    #-------------------------------------------------------------------------
    for app in apps:
        pdf.print_chapter('Report for Application: '+app["applicationName"],'')
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


def main():
    
    for report in args:
        if args[report] == True:
            exec(report+"()")
           

if __name__ == "__main__":
    main()
#raise SystemExit

