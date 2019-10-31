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


xtitle = ["ISO week number", "Applications", "Organisations"]
filename = "successmetrics.json"

with open(filename, 'r') as f:
    report = json.load(f)
    summary = report["summary"]
    apps = report["apps"]
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
def make_hor_line(fig,x0,y0,x1,y1,colour):
    # Add horizontal line to signal the target threshold
    fig.update_layout(
        shapes=[
            # Line Vertical
            #go.layout.Shape(
            #    type="line",
            #    x0=1,
            #    y0=0,
            #    x1=1,
            #    y1=2,
            #    line=dict(
            #        color="RoyalBlue",
            #        width=3
            #    )
            #),
            # Line Horizontal
            go.layout.Shape(
                type="line",
                x0=x0,
                y0=y0,
                x1=x1,
                y1=y1,
                line=dict(
                    color=colour,
                    width=4
                )
            )#,
            # Line Diagonal
            #go.layout.Shape(
            #    type="line",
            #    x0=4,
            #    y0=0,
            #    x1=6,
            #    y1=2,
            #    line=dict(
            #        color="MediumPurple",
            #        width=4,
            #        dash="dot",
            #    ),
            #),
        ]
    )

def make_chart(period, data, filename, title, target, xtitle):
    fig = go.Figure(
        data=[ go.Bar(x=period, y=data, text=data, textposition='auto') ], 
        layout_title_text=title
    )

    fig.update_layout(autosize=False, width=864, height=528, xaxis=go.layout.XAxis(title_text=xtitle))
    fig.update_xaxes(tickvals=period,automargin=True)

    if target != "0":    
        make_hor_line(fig,period[0],int(target),period[len(period)-1],int(target),"Red")
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



def output_pdf(pages, filename):
	pdf = FPDF()
	pdf.set_font('arial','B',12)
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

def adoption(target=0):
    pages = []
    scans = dict()
    j, graphNo = 0, 5
    
    printProgressBar(j, graphNo)
    #------------------------------------
    make_chart( 
        summary['weeks'], 
        summary['appOnboard'], 
        "AppsOnboarded.png", 
        "Number of apps onboarded (weekly view)", 
        target[0], 
        xtitle[0]
    )
    pages.append('AppsOnboarded.png')
    j +=1
    printProgressBar(j, graphNo)
    #------------------------------------
    make_chart(
        summary['weeks'], 
        summary['appNumberScan'], 
        "AppsScanning.png", 
        "Number of apps scanned per week", 
        "0", 
        xtitle[0]
    )
    pages.append('AppsScanning.png')
    j +=1
    printProgressBar(j, graphNo)
    #------------------------------------
    make_chart( 
        summary['weeks'], 
        summary['weeklyScans'], 
        "WeeklyScans.png", 
        "Total number of scans per week", 
        "0", 
        xtitle[0]
    )
    pages.append('WeeklyScans.png')
    j +=1
    printProgressBar(j, graphNo)
    #------------------------------------

    for app in apps:
        appName = app["applicationName"]

        scans.update({ appName: sum(app["summary"]["evaluationCount"]["rng"]) })

        make_chart( 
            summary['weeks'], 
            app['summary']['evaluationCount']['rng'], 
            f"{appName}_EvalCount.png", 
            f"Number of scans/week for app {appName}", 
            target[1], 
            xtitle[0]
        )
        pages.append( f"{appName}_EvalCount.png" )

        make_stacked_chart(
            summary['weeks'],
            [
                app['summary']['discoveredCounts']['TOTAL']['rng'],
                app['summary']['fixedCounts']['TOTAL']['rng'],
                app['summary']['waivedCounts']['TOTAL']['rng']
            ],
            ['Discovered','Fixed','Waived'],
            f"{appName}_DisFixWaiCount.png",
            f"Number of Discovered, Fixed, & Waived vulnerabilities for app {appName}",
            xtitle[0]
        )
        pages.append(f"{appName}_DisFixWaiCount.png")
    j +=1
    printProgressBar(j, graphNo)
    #------------------------------------
    make_chart( 
        list(scans.keys()), 
        list(scans.values()), 
        "AppsTotalScans.png", 
        "Total number of scans per app", 
        "0", 
        xtitle[1]
    )
    pages.append('AppsTotalScans.png')
    j +=1
    printProgressBar(j, graphNo)
    #------------------------------------
    output_pdf(pages, "adoption_report.pdf")

#---------------------------------
#PREVENTION: "To reduce the number of vulnerabilities passed from build to release"
#Generates open counts at build and at release per week (total, per org, per app) and compares them
#Tracks compliance percentage of maximum number of vulnerabilities at release stage per threat level
def prevention():
    print("Prevention report soon to be implemented")


#-------------------------------------------------------------------------
#REMEDIATION: "To reduce the number of vulnerabilities by x percentage"
#Generates discovered, fixed & waived counts/week (total, per org, per app). 
#Tracks compliance percentage of fix, waive & dealt-with percentage per week and threat level
#Generates open counts/week (total, per org, per app). 
#Displays current technical debt, and tracks how long (in hours) 
#would it take to deal with it at current dealt-with rate (for informational purposes).
#-------------------------------------------------------------------------
def remediation():
    pages, j, graphNo = [], 0, 7
    appName, orgName, OpeLow, OpeMod, OpeSev, OpeCri = [],[],[],[],[],[]

    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['weeks'],
        summary['openCountsAtTimePeriodEnd']['LIST'],
        ['Low','Moderate','Severe','Critical'],
        "OpenBacklog.png",
        "Number of open vulnerabilities (backlog) per week",
        xtitle[0]
    )
    pages.append('OpenBacklog.png')
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
       "Current_Open_Orgs.png", 
       "Current Total Number of Open vulnerabilities by organisation",
        xtitle[2]
    )
    pages.append("Current_Open_Orgs.png")
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
       "Current_Open_Apps.png", 
       "Current Total Number of Open vulnerabilities by application",
        xtitle[1]
    )
    pages.append("Current_Open_Apps.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['weeks'],
        [
            summary['discoveredCounts']['TOTAL'],
            summary['fixedCounts']['TOTAL'],
            summary['waivedCounts']['TOTAL']
        ],
       ['Discovered', 'Fixed', 'Waived'],
       "Total_DisFixWaiCount.png", 
       "Total Number of Discovered, Fixed & Waived vulnerabilities week-on-week",
        xtitle[0]
    )
    pages.append("Total_DisFixWaiCount.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['weeks'], 
        summary['discoveredCounts']['LIST'],
        ['Discovered Low', 'Discovered Moderate', 'Discovered Severe', 'Discovered Critical'],
        "Discovered_breakdown.png",
        "Total Number of Discovered vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("Discovered_breakdown.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['weeks'], 
        summary['fixedCounts']['LIST'],
        ['Fixed Low', 'Fixed Moderate', 'Fixed Severe', 'Fixed Critical'],
        "Fixed_breakdown.png",
        "Total Number of Fixed vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("Fixed_breakdown.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    make_stacked_chart(
        summary['weeks'], 
        summary['waivedCounts']['LIST'],
        ['Waived Low', 'Waived Moderate', 'Waived Severe', 'Waived Critical'],
        "Waived_breakdown.png",
        "Total Number of Waived vulnerabilities by severity week-on-week",
        xtitle[0]
    )
    pages.append("Waived_breakdown.png")
    j +=1
    printProgressBar(j,graphNo)
    #---------------------------------------------------------------------
    output_pdf(pages, "remediation_report.pdf")

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

i = True
while i==True:
    choice = input("\nFor Adoption report, press 1: \n"+
                   "For Prevention report, press 2: \n"+
                   "For Remediation report, press 3: \n"+
                   "For Enforcement report, press 4: \n"+
                   "For Hygiene report, press 5: \n"+
                   "To exit, press 0: \n")

    if choice == "1":
        choice = input("Do you want to set targets? (y/n): ")
        if choice == "y":
            target = []
            print("WARNING: a minimum of two data points (2 weeks of data) is needed to display the target line")
            target.append(input("\nWhat is the desired number of apps to be onboarded?: "))
            target.append(input("What is the desired number of scans/week per app?: "))
            adoption(target)

        if choice =="n":
            adoption(["0","0"])

        else:
            print("Incorrect option selected")

    if choice == "2":
        prevention()

    if choice == "3":
        remediation()

    if choice == "4":
        enforcement()

    if choice == "5":
        hygiene()

    if choice == "0":
        i = False



