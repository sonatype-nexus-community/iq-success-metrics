# Customer Success Metrics

## Overview

Nexus IQ Server has a number of REST APIs that allow you to automate certain tasks as well as quickly retrieve IQ server data. One of those APIs is the Success Metrics Data API which collects all the violations and other measurements and shares them as counters inside a JSON dictionary. In order to better capture the results, we have developed a Python script to collect, aggregate and process the counters into outcome-based metrics. We can use these outcome-based metrics to measure progression toward your PDOs.

## Explaining the Success Metrics Data API

The Success Metrics Data API returns policy evaluation, violation and remediation data, aggregated monthly or weekly. The API uses the following common language in its return values:

### API Legend:

* Threat Level Low - Policy Threat Level 1
* Threat Level Moderate - Policy Threat Level 2 - 3
* Threat Level Severe - Policy Threat Level 4 - 7
* Threat Level Critical - Policy Threat Level 8 - 10
* Security Violation - Violation for which the policy constraint was on the Security Vulnerability Severity Score
* License Violation - Violation for which the policy constraint was on the License or License Threat Group
* Quality Violation - Violation for which the policy constraint was on the Age or Relative Popularity of a component
* Other Violation - Violation for which the policy constraint was something other than a Secuity, License, or Quality constraint, such as a label

Here are the actual values returned from the REST call:

### Dimensional Data

* applicationId - Unique ID per application, assigned by IQ server
* applicationPublicId - ID, assigned by customer
* applicationName - Name, assigned by customer
* organizationId - Unique Organization ID, assigned by IQ server
* organizationName - Organization name, assigned by customer
* timePeriodStart - Start time period of aggregration of the data (usually weekly or monthly from this date). In ISO 8601 date format.

### Scan Data

* evaluationCount - Number of evaluations or scans for a particular application

### Violation Data

* Mean Time To Resolution (MTTR) in milliseconds for Low (Threat Level violation 1 ), Moderate (Threat Level violations 2-3), Severe (Threat Level violations 4-7), or Critical (Threat Level violations 8-10)
* mttrLowThreat
* mttrModerateThreat
* mttrSevereThreat
* mttrCriticalThreat

### Number of newly discovered Security/License/Quality/Other violations during the time period for Low/Moderate/Severe/Critical threat levels (Note: does not include violations that existed in previous time periods)

* discoveredCountSecurityLow
* discoveredCountSecurityModerate
* discoveredCountSecuritySevere
* discoveredCountSecurityCritical
* discoveredCountLicenseLow
* discoveredCountLicenseModerate
* discoveredCountLicenseSevere
* discoveredCountLicenseCritical
* discoveredCountQualityLow
* discoveredCountQualityModerate
* discoveredCountQualitySevere
* discoveredCountQualityCritical
* discoveredCountOtherLow
* discoveredCountOtherModerate
* discoveredCountOtherSevere
* discoveredCountOtherCritical

### Number of "fixed" Security/License/Quality/Other violations during the time period for Low/Moderate/Severe/Critical threat levels (Note: fixed is defined as a specific violation that existed in the immediately prior scan and now no longer appears in the subsequent scan)

* fixedCountSecurityLow
* fixedCountSecurityModerate
* fixedCountSecuritySevere
* fixedCountSecurityCritical
* fixedCountLicenseLow
* fixedCountLicenseModerate
* fixedCountLicenseSevere
* fixedCountLicenseCritical
* fixedCountQualityLow
* fixedCountQualityModerate
* fixedCountQualitySevere
* fixedCountQualityCritical
* fixedCountOtherLow
* fixedCountOtherModerate
* fixedCountOtherSevere
* fixedCountOtherCritical

### Number of waived Security/License/Quality/Other violations during the time period for Low/Moderate/Severe/Critical threat levels.

* waivedCountSecurityLow
* waivedCountSecurityModerate
* waivedCountSecuritySevere
* waivedCountSecurityCritical
* waivedCountLicenseLow
* waivedCountLicenseModerate
* waivedCountLicenseSevere
* waivedCountLicenseCritical
* waivedCountQualityLow
* waivedCountQualityModerate
* waivedCountQualitySevere
* waivedCountQualityCritical
* waivedCountOtherLow
* waivedCountOtherModerate
* waivedCountOtherSevere
* waivedCountOtherCritical

### Number of "open" Security/License/Quality/Other violations at the end of the time period for Low/Moderate/Severe/Critical threat levels.

Open counts accumulate from previous time periods (weeks/months) and constitute the technical debt backlog to fix/remediate.
For example, if you discovered 10 Security Critical violations each week for 3 weeks (total of 30 violations) and you fixed and/or waived a total of 10 Security Critical violations at the end of those 3 weeks,
the openCountAtTimePeriodEndSecurityCritical counter would show 20 (Security Critical open violations).

* openCountAtTimePeriodEndSecurityLow
* openCountAtTimePeriodEndSecurityModerate
* openCountAtTimePeriodEndSecuritySevere
* openCountAtTimePeriodEndSecurityCritical
* openCountAtTimePeriodEndLicenseLow
* openCountAtTimePeriodEndLicenseModerate
* openCountAtTimePeriodEndLicenseSevere
* openCountAtTimePeriodEndLicenseCritical
* openCountAtTimePeriodEndQualityLow
* openCountAtTimePeriodEndQualityModerate
* openCountAtTimePeriodEndQualitySevere
* openCountAtTimePeriodEndQualityCritical
* openCountAtTimePeriodEndOtherLow
* openCountAtTimePeriodEndOtherModerate
* openCountAtTimePeriodEndOtherSevere
* openCountAtTimePeriodEndOtherCritical

## Understanding the Python script

Though the source code can be modified to suit your particular needs if necessary, the following is an explaination of the script in its current form.

The script is actually two different files: `success_metrics.py`  and `reports.py` 

    `success_metrics.py` makes the API calls according to the command-line parameters and it will process the counters to generate the more relevant outcome-based Success Metrics, returning them as a JSON dictionary on the screen (by default). It is recommended to use the -v option to save the JSON dictionary to the successmetrics.json file.

    `reports.py` is an interactive script that consumes JSON files generated by `success_metrics.py` and produces different types of reports and graphs depending on the Primary Desired Outcome (PDO). The main output will be a `successmetrics.pdf` report containing graphs and data relevant to the chosen PDO. Additionally, all graphs are also saved to individual .png files for further re-use in presentations.

### Pre-requisites

This script utilizes Python 3. If you don't have Python 3 installed, you can follow this step-by-step guide.

The script imports a number of libraries in addition to standard Python ones, for example the pandas library.

To install those necessary libraries, you just need to do the following for each missing library:

First, if you don't have pip installed, you can follow these installation instructions.

Then you can simply run the following commands:

```
pip3 install pandas

pip3 install plotly

pip3 install fpdf 

pip3 install requests 

pip3 install psutil
```

You will also need to install Orca for the script to be able to programatically save the plotly images to disk and for these to be added to the pdf report. To do this, follow the Installation notes for Method 4: Standalone binaries inside the README file in Orca's github. If you have questions regarding these instructions please contact Sonatype Customer Success. Below a screenshot for the Mac OS:

### Usage

You can get started by running the following command to display all the available options:

```
python3 success_metrics -h

Usage: python3 success_metrics.py [-h] [-a AUTH] [-s SCOPE] [-u URL] [-i APPID] [-o ORGID] [-p] [-v]

The optional arguments are:
-h, --help (shows this help message and exits)
-a AUTH, --auth AUTH (in the format user:password, by default admin:admin123 )
-s SCOPE, --scope SCOPE (number of weeks from current one to gather data from. Default value is six weeks)
-u URL, --url URL (URL for IQ server, by default http://localhost:8070 )
-i APPID, --appId APPID (list of application IDs, application Names, application Public IDs or combination thereof to filter from all available data. Default is all available data)
-o ORGID, --orgId ORGID (list of organization IDs, organization Names or combination thereof to filter from all available data. Default is all available data)
-p, --pretty (indents the JSON printout 4 spaces. Default is no indentation)
-v, --save (saves all data into JSON file successmetrics.json. Default is to print out on screen)
```

Two valid examples would be:

`python3 success_metrics.py`

This collects the past six weeks of data for all applications in all organizations, processes them and prints them in non-indented JSON format on screen. This assumes the default user, password and IQ server's URL.

`python3 success_metrics.py -a administrator:password1234 -s 10 -u 'http://123.456.789.0:8070' -i 'd8f63854f4ea4405a9600e34f4d4514e','Test App1','MyApp3' -o 'c6f2775a45d44d43a32621536e638a8e', 'My Org' -p -v`

This collects the past ten weeks of data for the three applications listed ('d8f63854f4ea4405a9600e34f4d4514e','Test App1','MyApp3'), irrespective of them belonging to any particular organization. In addition, this also collects the past ten weeks of data for all the applications under organizations 'c6f2775a45d44d43a32621536e638a8e' and 'My Org'. The filtering does an OR filtering, so the collected data will be the union of the three apps with the two organizations. Then it processes the data, prints out the results in the "pretty" format (indented 4 spaces) and saves the non-indented data into the JSON file successmetrics.json 


Once you have generated the `successmetrics.json` file, you can pass it to the reports.py script.

Usage: `python3 reports.py` 

The script will read the `successmetrics.json` file and present you with an interactive menu:

```
For Adoption report, press 1:

For Prevention report, press 2:

For Remediation report, press 3:

For Enforcement report, press 4:

For Hygiene report, press 5:

To exit, press 0:
```

By entering the desired number, a targeted report will be produced in .pdf format and all graphs contained in the report will also be individually generated as .png files for later use in presentations.

### Understanding the `successmetrics.json` file

The JSON file will be a list of applications and inside each element of that list (each app), there is a dictionary containing all the data. A sample of the tree structure of the JSON file for four apps is shown below:

We can see that first element in the list (number 0), has an `applicationId, applicationPublicId, applicationName, organizationId, organizationName` to be able to identify this particular application within a specific organization.

Then we can see the following:

* `aggregations`: this is the raw data collected by the API call. All the values inside aggregations have been explained in section 2. Explaining the Success Metrics Data API
* `summary`: this is the summary of all the outcome-based success metrics resulting from processing the raw data from the API call. More information later below.
* `weeksInScope`: this is the range of weeks in scope, in ISO format (week number). This was selected when running the success_metrics.py script and was set by default to 6 weeks, so if we were in the middle of week 38, we would request the IQ server for weeks 32, 33, 34, 35, 36 and 37 (the past six fully completed weeks).
* `orgNames`: this is a list of all the organization names within scope.
* `appNames`: this is a list of all the application names within scope.
* `appNumberScan`: this is a list of the number of applications that have been scanned in each of the weeks in scope. IMPORTANT: due to the looping nature of the code, the overall accurate result is only available in the appNumberScan property of the last element in the list, in this case the fourth element in the list (number 3).
* `appOnboard`: this is a list of the number of applications onboarded in the IQ server in each of the weeks in scope. IMPORTANT: due to the looping nature of the code, the overall accurate result is only available in the appOnboard property of the last element in the list, in this case the fourth element in the list (number 3).

Now it is time to explore the summary dictionary in more detail:

Below are each one of them explained:
* `weeks`: this is a list of all the weeks in ISO format that contain data. It is possible that a particular app was not scanned during one or more of the weeks in scope
* `fixedRate`: this is the YTD weekly rolling average (in percentage) of the Fixed Rate for Security/License/Quality/Other vulnerabilities combined, for all Low/Moderate/Severe/Critical threat levels combined for that particular app. fixedRate is calculated as fixedCounts / openCountsAtTimePeriodEnd (for the previous week) in percentage. For example if you fixed 5 Security Critical vulnerabilities in week 2 and at the end of week 1 you had left 50 open, the Fixed Rate would be 10%.
* `waivedRate`: this is the YTD weekly rolling average (in percentage) of the Waived Rate for Security/License/Quality/Other vulnerabilities combined, for all Low/Moderate/Severe/Critical threat levels combined for that particular app. waivedRate is calculated as waivedCounts / openCountsAtTimePeriodEnd (for the previous week) in percentage. For example if you waived 5 Security Critical vulnerabilities in week 2 and at the end of week 1 you had left 50 open, the Waived Rate would be 10%.
* `DealtRate`: this is the YTD weekly rolling average (in percentage) of the Dealt-with Rate for Security/License/Quality/Other vulnerabilities combined, for all Low/Moderate/Severe/Critical threat levels combined for that particular app. DealtRate is calculated as (fixedCounts + waivedCounts) / openCountsAtTimePeriodEnd (for the previous week) in percentage. For example if you fixed 5 and waived 15 Security Critical vulnerabilities in week 2 and at the end of week 1 you had left 100 open, the Dealt-with Rate would be 20% for Security Critical vulnerabilities.
* `FixPercent`: this is the unitary percentage (0.5 = 50%) of all dealt-with vulnerabilities that were fixed for that particular app.
* `WaiPercent` : this is the unitary percentage (0.5 = 50%) of all dealt-with vulnerabilities that were waived for that particular app. Please note that FixPercent + WaiPercent = 1 

The following metrics are dictionaries and inside them, they have the avg (average value) and rng (range, or isolated values per week of data) parameters. Some of them go into more detail, with a selection of TOTAL, SECURITY, LICENSE, QUALITY and OTHER violation types and LOW, MODERATE, SEVERE and CRITICAL threat levels.

* `mttrLowThreat`: this is the Mean Time To Resolution (measured in days instead of milliseconds) for Low threat level violations for that particular app. avg provides the overall average of the weeks in scope and rng provides the isolated MTTR values.
* `mttrModerateThreat`: this is the Mean Time To Resolution (measured in days instead of milliseconds) for Moderate threat level violations for that particular app. avg provides the overall average of the weeks in scope and rng provides the isolated MTTR values.
* `mttrSevereThreat`: this is the Mean Time To Resolution (measured in days instead of milliseconds) for Severe threat level violations for that particular app. avg provides the overall average of the weeks in scope and rng provides the isolated MTTR values.
* `mttrCriticalThreat`: this is the Mean Time To Resolution (measured in days instead of milliseconds) for Critical threat level violations for that particular app. avg provides the overall average of the weeks in scope and rng provides the isolated MTTR values.
* `evaluationCount`: this is the number of evaluations or scans that were performed on that particular app. avg provides the overall average number of scans over the weeks in scope and rng provides the isolated scans/week.
* `discoveredCounts`: this is the number of discovered vulnerabilities of a particular type (TOTAL, SECURITY, LICENSE, QUALITY, OTHER), of a particular threat level (TOTAL, LOW, MODERATE, SEVERE, CRITICAL) for that particular app. avg provides the overall average number of vulnerabilities of that type and threat level and rng provides the isolated number per week.
* `fixedCounts`: this is the number of fixed vulnerabilities of a particular type (TOTAL, SECURITY, LICENSE, QUALITY, OTHER), of a particular threat level (TOTAL, LOW, MODERATE, SEVERE, CRITICAL) for that particular app. avg provides the overall average number of vulnerabilities of that type and threat level and rng provides the isolated number per week.
* `waivedCounts`: this is the number of waived vulnerabilities of a particular type (TOTAL, SECURITY, LICENSE, QUALITY, OTHER), of a particular threat level (TOTAL, LOW, MODERATE, SEVERE, CRITICAL) for that particular app. avg provides the overall average number of vulnerabilities of that type and threat level and rng provides the isolated number per week.
* `openCountsAtTimePeriodEnd`: this is the number of open vulnerabilities of a particular type (TOTAL, SECURITY, LICENSE, QUALITY, OTHER), of a particular threat level (TOTAL, LOW, MODERATE, SEVERE, CRITICAL) for that particular app. avg provides the overall average number of vulnerabilities of that type and threat level and rng provides the isolated number per week. Open counts accumulate from previous time periods (weeks/months) and constitute the technical debt backlog to fix/remediate. For example, if you discovered 10 Security Critical violations each week for 3 weeks (total of 30 violations) and you fixed and/or waived a total of 10 Security Critical violations at the end of those 3 weeks, the openCountAtTimePeriodEndSecurityCritical counter would show 20 (Security Critical open violations).

### Understanding the successmetrics.pdf report

TBD

## Contributing

If you as well want to speed up the pace of software development by working on this project, jump on in! Before you start work, create
a new issue, or comment on an existing issue, to let others know you are!

## The Fine Print

It is worth noting that this is **NOT SUPPORTED** by Sonatype, and is a contribution of ours to the open source community (read: you!)

Don't worry, using this community item does not "void your warranty". In a worst case scenario, you may be asked by the Sonatype Support team to remove the community item in order to determine the root cause of any issues.

Remember:

* Use this contribution at the risk tolerance that you have
* Do NOT file Sonatype support tickets related to Cabal support in regard to this plugin
* DO file issues here on GitHub, so that the community can pitch in

Phew, that was easier than I thought. Last but not least of all:

Have fun creating and using this plugin and the Nexus platform, we are glad to have you here!

## Getting help

Looking to contribute to our code but need some help? There's a few ways to get information:

* Chat with us on [Gitter](https://gitter.im/sonatype/nexus-developers)
