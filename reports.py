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


xtitle = ["ISO week number", "Applications", "Organisations"]
filename = "./output/successmetrics.json"

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
        self.cell(60, 10, 'POC report', 1, 0, 'C')
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
        self.add_page()
        self.chapter_title(title)
        self.chapter_body(content)


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

def adoption():
    pages = []
    scans = dict()
    j, graphNo = 0, 5
    
    printProgressBar(j, graphNo)
    #------------------------------------
    make_chart( 
        summary['weeks'], 
        summary['appOnboard'], 
        "./output/AppsOnboarded.png", 
        "Number of apps onboarded (weekly view)", 
        xtitle[0]
    )
    pages.append('./output/AppsOnboarded.png')
    j +=1
    printProgressBar(j, graphNo)
    #------------------------------------
    make_chart(
        summary['weeks'], 
        summary['appNumberScan'], 
        "./output/AppsScanning.png", 
        "Number of apps scanned per week", 
        xtitle[0]
    )
    pages.append('./output/AppsScanning.png')
    j +=1
    printProgressBar(j, graphNo)
    #------------------------------------
    make_chart( 
        summary['weeks'], 
        summary['weeklyScans'], 
        "./output/WeeklyScans.png", 
        "Total number of scans per week", 
        xtitle[0]
    )
    pages.append('./output/WeeklyScans.png')
    j +=1
    printProgressBar(j, graphNo)
    #------------------------------------

    for app in apps:
        appName = app["applicationName"]

        scans.update({ appName: sum(app["summary"]["evaluationCount"]["rng"]) })

        make_chart( 
            summary['weeks'], 
            app['summary']['evaluationCount']['rng'], 
            f"./output/{appName}_EvalCount.png", 
            f"Number of scans/week for app {appName}", 
            xtitle[0]
        )
        pages.append( f"./output/{appName}_EvalCount.png" )

        make_stacked_chart(
            summary['weeks'],
            [
                app['summary']['discoveredCounts']['TOTAL']['rng'],
                app['summary']['fixedCounts']['TOTAL']['rng'],
                app['summary']['waivedCounts']['TOTAL']['rng']
            ],
            ['Discovered','Fixed','Waived'],
            f"./output/{appName}_DisFixWaiCount.png",
            f"Number of Discovered, Fixed, & Waived vulnerabilities for app {appName}",
            xtitle[0]
        )
        pages.append(f"./output/{appName}_DisFixWaiCount.png")
    j +=1
    printProgressBar(j, graphNo)
    #------------------------------------
    make_chart( 
        list(scans.keys()), 
        list(scans.values()), 
        "./output/AppsTotalScans.png", 
        "Total number of scans per app", 
        xtitle[1]
    )
    pages.append('./output/AppsTotalScans.png')
    j +=1
    printProgressBar(j, graphNo)
    #------------------------------------
    output_pdf(pages, "./output/adoption_report.pdf")


#-------------------------------------------------------------------------
#REMEDIATION: "To reduce the number of vulnerabilities by x percentage"
#Generates discovered, fixed & waived counts/week (total, per org, per app). 
#Tracks compliance percentage of fix, waive & dealt-with percentage per week and threat level
#Generates open counts/week (total, per org, per app). 
#Displays current technical debt, and tracks how long (in hours) 
#would it take to deal with it at current dealt-with rate (for informational purposes).
#-------------------------------------------------------------------------
def remediation():
    pages, j, graphNo = [], 0, 13
    appName, orgName, OpeLow, OpeMod, OpeSev, OpeCri, mttrLow, mttrMod, mttrSev, mttrCri = [],[],[],[],[],[],[],[],[],[]

    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['weeks'],
        summary['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/OpenBacklog.png",
        "Number of open vulnerabilities (backlog) per week",
        xtitle[0]
    )
    pages.append('./output/OpenBacklog.png')
    j +=1
    printProgressBar(j,graphNo)
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
    pages.append("./output/Current_Open_Orgs.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    for app in apps:
        appName.append(app["applicationName"])
        OpeLow.append(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["LOW"]["rng"][len(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["LOW"]["rng"])-1])
        OpeMod.append(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["MODERATE"]["rng"][len(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["MODERATE"]["rng"])-1])
        OpeSev.append(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["SEVERE"]["rng"][len(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["SEVERE"]["rng"])-1])
        OpeCri.append(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["CRITICAL"]["rng"][len(app["summary"]["openCountsAtTimePeriodEnd"]["TOTAL"]["CRITICAL"]["rng"])-1])
    
    make_stacked_chart(
        appName,
        [
            OpeLow,
            OpeMod,
            OpeSev,
            OpeCri
        ],
       ['Low', 'Moderate', 'Severe', 'Critical'],
       "./output/Current_Open_Apps.png", 
       "Current Total Number of Open vulnerabilities by application",
        xtitle[1]
    )
    pages.append("./output/Current_Open_Apps.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    for app in apps:
        make_chart( 
            app["summary"]['weeks'], 
            app["summary"]['fixedRate'], 
            "./output/Fixed_Rate_"+app["applicationName"]+".png", 
            "Fixed rate for "+app["applicationName"]+" week-on-week", 
            xtitle[0]
        )
        pages.append("./output/Fixed_Rate_"+app["applicationName"]+".png")
    j +=1
    printProgressBar(j, graphNo)
    #---------------------------------------------------------------------
    for app in apps:
        make_chart( 
            app["summary"]['weeks'], 
            app["summary"]['waivedRate'], 
            "./output/Waived_Rate_"+app["applicationName"]+".png", 
            "Waived rate for "+app["applicationName"]+" week-on-week", 
            xtitle[0]
        )
        pages.append("./output/Waived_Rate_"+app["applicationName"]+".png")
    j +=1
    printProgressBar(j, graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['weeks'],
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
    pages.append("./output/Total_DisFixWaiCount.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['weeks'], 
        summary['discoveredCounts']['LIST'],
        ['Discovered Low', 'Discovered Moderate', 'Discovered Severe', 'Discovered Critical'],
        "./output/Discovered_breakdown.png",
        "Total Number of Discovered vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("./output/Discovered_breakdown.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['weeks'], 
        summary['fixedCounts']['LIST'],
        ['Fixed Low', 'Fixed Moderate', 'Fixed Severe', 'Fixed Critical'],
        "./output/Fixed_breakdown.png",
        "Total Number of Fixed vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("./output/Fixed_breakdown.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['weeks'], 
        summary['waivedCounts']['LIST'],
        ['Waived Low', 'Waived Moderate', 'Waived Severe', 'Waived Critical'],
        "./output/Waived_breakdown.png",
        "Total Number of Waived vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("./output/Waived_breakdown.png")
    j +=1
    printProgressBar(j,graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        summary['weeks'], 
        summary['mttrLowThreat'], 
        "./output/MTTR_Low.png", 
        "MTTR (in days) for all Low Threat vulnerabilities week-on-week", 
        xtitle[0]
    )
    pages.append('./output/MTTR_Low.png')
    j +=1
    printProgressBar(j, graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        summary['weeks'], 
        summary['mttrModerateThreat'], 
        "./output/MTTR_Moderate.png", 
        "MTTR (in days) for all Moderate Threat vulnerabilities week-on-week", 
        xtitle[0]
    )
    pages.append('./output/MTTR_Moderate.png')
    j +=1
    printProgressBar(j, graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        summary['weeks'], 
        summary['mttrSevereThreat'], 
        "./output/MTTR_Severe.png", 
        "MTTR (in days) for all Severe Threat vulnerabilities week-on-week", 
        xtitle[0]
    )
    pages.append('./output/MTTR_Severe.png')
    j +=1
    printProgressBar(j, graphNo)
     #---------------------------------------------------------------------
    make_chart( 
        summary['weeks'], 
        summary['mttrCriticalThreat'], 
        "./output/MTTR_Critical.png", 
        "MTTR (in days) for all Critical Threat vulnerabilities week-on-week", 
        xtitle[0]
    )
    pages.append('./output/MTTR_Critical.png')
    j +=1
    printProgressBar(j, graphNo)
    #---------------------------------------------------------------------
    output_pdf(pages, "./output/remediation_report.pdf")


#---------------------------------
#PREVENTION: "To reduce the number of vulnerabilities passed from build to release"
#Generates open counts at build and at release per week (total, per org, per app) and compares them
#Tracks compliance percentage of maximum number of vulnerabilities at release stage per threat level
def prevention():
    print("Prevention report soon to be implemented")



#---------------------------------
#ENFORCEMENT: To control a specific metric regularly, for example: 
# number of waivers, MTTR at certain value per threat level, 
# CVSS==10 vulnerabilities below threshold or fixed before x time
# Generates the specific metric (Custom)
#Tracks deviation level
def enforcement():
    print("Enforcement report soon to be implemented")

#---------------------------------
#HYGIENE: "To not use any components older than a certain age or below a certain popularity"
#Generates age & popularity report
#Tracks compliance percentage for age & popularity thresholds
def hygiene():
    print("Hygiene report soon to be implemented")

#---------------------------------


#-------------------------------------------------------------------------
#LICENCE: "To reduce the number of licensing vulnerabilities by x percentage"
#Same as Remediation report but only for Licensing vulnerabilities
#Generates discovered, fixed & waived counts/week (total, per org, per app). 
#Tracks compliance percentage of fix, waive & dealt-with percentage per week and threat level
#Generates open counts/week (total, per org, per app). 
#Displays current technical debt, and tracks how long (in hours) 
#would it take to deal with it at current dealt-with rate (for informational purposes).
#-------------------------------------------------------------------------
def licence():
    pages, j, graphNo = [], 0, 7
    appName, orgName, OpeLow, OpeMod, OpeSev, OpeCri, mttrLow, mttrMod, mttrSev, mttrCri = [],[],[],[],[],[],[],[],[],[]

    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        licences['weeks'],
        licences['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/Open_Backlog_Lic.png",
        "Number of open vulnerabilities (backlog) per week",
        xtitle[0]
    )
    pages.append('./output/Open_Backlog_Lic.png')
    j +=1
    printProgressBar(j,graphNo)
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
       "./output/Current_Open_Orgs_Lic.png", 
       "Current Total Number of Open vulnerabilities by organisation",
        xtitle[2]
    )
    pages.append("./output/Current_Open_Orgs_Lic.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    for app in apps:
        appName.append(app["applicationName"])
        OpeLow.append(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["LOW"]["rng"][len(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["LOW"]["rng"])-1])
        OpeMod.append(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["MODERATE"]["rng"][len(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["MODERATE"]["rng"])-1])
        OpeSev.append(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["SEVERE"]["rng"][len(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["SEVERE"]["rng"])-1])
        OpeCri.append(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["CRITICAL"]["rng"][len(app["licences"]["openCountsAtTimePeriodEnd"]["LICENSE"]["CRITICAL"]["rng"])-1])
    
    make_stacked_chart(
        appName,
        [
            OpeLow,
            OpeMod,
            OpeSev,
            OpeCri
        ],
       ['Low', 'Moderate', 'Severe', 'Critical'],
       "./output/Current_Open_Apps_Lic.png", 
       "Current Total Number of Open vulnerabilities by application",
        xtitle[1]
    )
    pages.append("./output/Current_Open_Apps_Lic.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    #---------------------------------------------------------------------
    make_stacked_chart(
        licences['weeks'],
        [
            licences['discoveredCounts']['TOTAL'],
            licences['fixedCounts']['TOTAL'],
            licences['waivedCounts']['TOTAL']
        ],
       ['Discovered', 'Fixed', 'Waived'],
       "./output/Total_DisFixWaiCount_Lic.png", 
       "Total Number of Discovered, Fixed & Waived vulnerabilities week-on-week",
        xtitle[0]
    )
    pages.append("./output/Total_DisFixWaiCount_Lic.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        licences['weeks'], 
        licences['discoveredCounts']['LIST'],
        ['Discovered Low', 'Discovered Moderate', 'Discovered Severe', 'Discovered Critical'],
        "./output/Discovered_breakdown_Lic.png",
        "Total Number of Discovered vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("./output/Discovered_breakdown_Lic.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        licences['weeks'], 
        licences['fixedCounts']['LIST'],
        ['Fixed Low', 'Fixed Moderate', 'Fixed Severe', 'Fixed Critical'],
        "./output/Fixed_breakdown_Lic.png",
        "Total Number of Fixed vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("./output/Fixed_breakdown_Lic.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        licences['weeks'], 
        licences['waivedCounts']['LIST'],
        ['Waived Low', 'Waived Moderate', 'Waived Severe', 'Waived Critical'],
        "./output/Waived_breakdown_Lic.png",
        "Total Number of Waived vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("./output/Waived_breakdown_Lic.png")
    j +=1
    printProgressBar(j,graphNo)
     #---------------------------------------------------------------------
    output_pdf(pages, "./output/licence_report.pdf")
#-------------------------------------------------------------------------
#SECURITY: "To reduce the number of security vulnerabilities by x percentage"
#Same as Remediation report but only for security vulnerabilities
#Generates discovered, fixed & waived counts/week (total, per org, per app). 
#Tracks compliance percentage of fix, waive & dealt-with percentage per week and threat level
#Generates open counts/week (total, per org, per app). 
#Displays current technical debt, and tracks how long (in hours) 
#would it take to deal with it at current dealt-with rate (for informational purposes).
#-------------------------------------------------------------------------
def security():
    pages, j, graphNo = [], 0, 7
    appName, orgName, OpeLow, OpeMod, OpeSev, OpeCri, mttrLow, mttrMod, mttrSev, mttrCri = [],[],[],[],[],[],[],[],[],[]

    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        Security['weeks'],
        Security['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "./output/Open_Backlog_Sec.png",
        "Number of open vulnerabilities (backlog) per week",
        xtitle[0]
    )
    pages.append('./output/Open_Backlog_Sec.png')
    j +=1
    printProgressBar(j,graphNo)
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
       "./output/Current_Open_Orgs_Sec.png", 
       "Current Total Number of Open vulnerabilities by organisation",
        xtitle[2]
    )
    pages.append("./output/Current_Open_Orgs_Sec.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    for app in apps:
        appName.append(app["applicationName"])
        OpeLow.append(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["LOW"]["rng"][len(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["LOW"]["rng"])-1])
        OpeMod.append(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["MODERATE"]["rng"][len(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["MODERATE"]["rng"])-1])
        OpeSev.append(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["SEVERE"]["rng"][len(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["SEVERE"]["rng"])-1])
        OpeCri.append(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["CRITICAL"]["rng"][len(app["security"]["openCountsAtTimePeriodEnd"]["SECURITY"]["CRITICAL"]["rng"])-1])
    
    make_stacked_chart(
        appName,
        [
            OpeLow,
            OpeMod,
            OpeSev,
            OpeCri
        ],
       ['Low', 'Moderate', 'Severe', 'Critical'],
       "./output/Current_Open_Apps_Sec.png", 
       "Current Total Number of Open vulnerabilities by application",
        xtitle[1]
    )
    pages.append("./output/Current_Open_Apps_Sec.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    #---------------------------------------------------------------------
    make_stacked_chart(
        Security['weeks'],
        [
            Security['discoveredCounts']['TOTAL'],
            Security['fixedCounts']['TOTAL'],
            Security['waivedCounts']['TOTAL']
        ],
       ['Discovered', 'Fixed', 'Waived'],
       "./output/Total_DisFixWaiCount_Sec.png", 
       "Total Number of Discovered, Fixed & Waived vulnerabilities week-on-week",
        xtitle[0]
    )
    pages.append("./output/Total_DisFixWaiCount_Sec.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        Security['weeks'], 
        Security['discoveredCounts']['LIST'],
        ['Discovered Low', 'Discovered Moderate', 'Discovered Severe', 'Discovered Critical'],
        "./output/Discovered_breakdown_Sec.png",
        "Total Number of Discovered vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("./output/Discovered_breakdown_Sec.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        Security['weeks'], 
        Security['fixedCounts']['LIST'],
        ['Fixed Low', 'Fixed Moderate', 'Fixed Severe', 'Fixed Critical'],
        "./output/Fixed_breakdown_Sec.png",
        "Total Number of Fixed vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("./output/Fixed_breakdown_Sec.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        Security['weeks'], 
        Security['waivedCounts']['LIST'],
        ['Waived Low', 'Waived Moderate', 'Waived Severe', 'Waived Critical'],
        "./output/Waived_breakdown_Sec.png",
        "Total Number of Waived vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("./output/Waived_breakdown_Sec.png")
    j +=1
    printProgressBar(j,graphNo)
     #---------------------------------------------------------------------
    #---------------------------------------------------------------------

    output_pdf(pages, "./output/security_report.pdf")

#-------------------------------------------------------------------------
#POC: "To provide a report at the end of a Proof-of-Concept (POC)"
#-------------------------------------------------------------------------
    
# Instantiation of inherited class
def poc():
    pdf = PDF()
    pdf.alias_nb_pages()
    dict1 = {"Apps onboarded" : "20", "Number of scans" : "34"}
    dict2 = {"Open vulnerabilities" : "502" , "Fixed vulnerabilities" : "234", "Waived vulnerabilities" : "39"}
    pdf.print_chapter('Adoption Report', dict1)
    pdf.print_chapter('Remediation Report', dict2)
    pdf.output('./output/poc_report.pdf', 'F')


#-------------------------------------------------------------------------



def main():
    parser = argparse.ArgumentParser(description='get some reports')
    parser.add_argument('-a','--adoption',   help='generate adoption report', action='store_true', required=False)
    parser.add_argument('-r','--remediation',  help='generate remediation report', action='store_true', required=False)
    parser.add_argument('-e','--enforcement',    help='generate enforcement report', action='store_true', required=False)
    parser.add_argument('-p','--prevention',  help='generate prevention report', action='store_true', required=False)
    parser.add_argument('-hyg','--hygiene',  help='generate hygiene report', action='store_true', required=False)
    parser.add_argument('-l','--licence', help='generate remediation report only for licence violations', action='store_true', required=False)
    parser.add_argument('-s','--security', help='generate remediation report only for security violations', action='store_true', required=False)
    parser.add_argument('-poc','--poc', help='generate a Proof-of-Concept report', action='store_true', required=False)


    args = vars(parser.parse_args())
    
    for report in args:
        if args[report] == True:
            exec(report+"()")
           

if __name__ == "__main__":
    main()
#raise SystemExit

