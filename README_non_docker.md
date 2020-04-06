# IQ Success Metrics

[![CircleCI](https://circleci.com/gh/sonatype-nexus-community/iq-success-metrics.svg?style=svg)](https://circleci.com/gh/sonatype-nexus-community/iq-success-metrics)

## Overview

Nexus IQ Server has a number of [REST APIs](https://help.sonatype.com/iqserver/automating/rest-apis) that allow you to automate certain tasks as well as quickly retrieve IQ server data. One of those APIs is the [Success Metrics Data API](https://help.sonatype.com/iqserver/automating/rest-apis/success-metrics-data-rest-api---v2) which collects all the violations and other measurements and shares them as counters inside a JSON dictionary. In order to better capture the results, we have developed a Python script to collect, aggregate and process the counters into outcome-based metrics. We can use these outcome-based metrics to measure progression toward your PDOs.

## Explaining the Success Metrics Data API

The [Success Metrics Data API](https://help.sonatype.com/iqserver/automating/rest-apis/success-metrics-data-rest-api---v2) returns policy evaluation, violation and remediation data, aggregated monthly or weekly. The API uses the following common language in its return values:

### API Legend:

* Threat Level Low - Policy Threat Level 1
* Threat Level Moderate - Policy Threat Level 2 - 3
* Threat Level Severe - Policy Threat Level 4 - 7
* Threat Level Critical - Policy Threat Level 8 - 10
* Security Violation - Violation for which the policy constraint was on the Security Vulnerability Severity Score
* License Violation - Violation for which the policy constraint was on the License or License Threat Group
* Quality Violation - Violation for which the policy constraint was on the Age or Relative Popularity of a component
* Other Violation - Violation for which the policy constraint was something other than a Security, License, or Quality constraint, such as a label

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

`success_metrics.py` makes the API calls according to the command-line parameters and it will process the counters to generate the more relevant outcome-based Success Metrics, returning them as a JSON dictionary called successmetrics.json.

`reports.py` consumes the JSON file generated by `success_metrics.py` and produces different types of reports and graphs depending on the Primary Desired Outcome (PDO). The main output will be a `successmetrics.pdf` report containing graphs and data relevant to the chosen PDO. Additionally, all graphs are also saved to individual .png files for further re-use in presentations.

### Pre-requisites

First of all, it is indispensable to enable Success Metrics collection in your IQ server. To do this, go to System Preferences (the little cog) and select Success Metrics from the options. Then click on Enable.

This script utilizes Python 3. If you don't have Python 3 installed, you can follow [this step-by-step guide.](https://realpython.com/installing-python/)


The script imports a number of libraries in addition to standard Python ones, for example the fpdf library.

To install those necessary libraries, you just need to do the following for each missing library:

First, if you don't have pip installed, you can follow [these installation instructions.](https://pip.pypa.io/en/stable/installing/)

Then you can simply run the following commands:

```
pip3 install plotly

pip3 install fpdf 

pip3 install requests 

pip3 install psutil
```

You will also need to [install Orca](https://github.com/plotly/orca) for the script to be able to programatically save the plotly images to disk and for these to be added to the pdf report. To do this, follow the Installation notes for Method 4: Standalone binaries inside the README file in Orca's github. If you have questions regarding these instructions please contact Sonatype Customer Success. 


Another alternative is to install the required dependencies using the [requirements.txt](requirements.txt) file at the root of this project, e.g.:

    pip3 install -r requirements.txt
    
  A virtual environment with these requirements can be created and activated using the script: `.circleci/ci-setup.sh`.      

### Usage

You can get started by running the following command to display all the available options:

```
python3 success_metrics.py -h

Usage: python3 success_metrics.py [-h] [-a AUTH] [-s SCOPE] [-u URL] [-i APPID] [-o ORGID] [-p]

The optional arguments are:
-h, --help (shows this help message and exits)
-a AUTH, --auth AUTH (in the format user:password, by default admin:admin123 )
-s SCOPE, --scope SCOPE (number of weeks from current one to gather data from. Default value is six weeks)
-u URL, --url URL (URL for IQ server, by default http://localhost:8070 )
-i APPID, --appId APPID (list of application IDs, application Names, application Public IDs or combination thereof to filter from all available data. Default is all available data)
-o ORGID, --orgId ORGID (list of organization IDs, organization Names or combination thereof to filter from all available data. Default is all available data)
-p, --pretty (indents the JSON printout 4 spaces. Default is no indentation)
```

Two valid examples would be:

`python3 success_metrics.py`

This collects the past six weeks of data for all applications in all organizations, processes them and saves them in non-indented JSON format in successmetrics.json. This assumes the default user, password and IQ server's URL.

`python3 success_metrics.py -a administrator:password1234 -s 10 -u http://123.456.789.0:8070 -i 'd8f63854f4ea4405a9600e34f4d4514e','Test App1','MyApp3' -o 'c6f2775a45d44d43a32621536e638a8e','My Org' -p`

This collects the past ten weeks of data for the three applications listed ('d8f63854f4ea4405a9600e34f4d4514e','Test App1','MyApp3'), irrespective of them belonging to any particular organization. In addition, this also collects the past ten weeks of data for all the applications under organizations 'c6f2775a45d44d43a32621536e638a8e' and 'My Org'. The filtering does an OR filtering, so the collected data will be the union of the three apps with the two organizations. Then it processes the data, indents the results in the "pretty" format (indented 4 spaces) and saves it into the JSON file successmetrics.json 


Once you have generated the `successmetrics.json` file, you can pass it to the reports.py script.


```
python3 reports.py -h

Usage: python3 reports.py [-h] [-a] [-r] [-e] [-p] [-hyg] [-l] [-s]

The optional arguments are:
  -h, --help         show this help message and exit
  -a, --adoption     generates adoption report
  -r, --remediation  generates remediation report
  -e, --enforcement  generates enforcement report
  -p, --prevention   generates prevention report
  -hyg, --hygiene    generates hygiene report
  -l, --licence      generates remediation report only for licence violations
  -s, --security     generates remediation report only for security violations
  -t, --tables       generates a report in table format
```

By using the correct switches, a targeted report will be produced in .pdf format and all graphs contained in the report will also be individually generated as .png files for later use in presentations. 
#### Please note that if no switches are used, no reports will be generated by default.


### Understanding the `successmetrics.json` file

The successmetrics.json file is currently composed of four dictionaries: 

* `summary`: this is the overall summary that collates and aggregates all the data together, giving the global view. This dictionary is the main one used for generating the global reports.
* `apps`: this is a list of all the applications within scope. It contains the raw data coming from the API call (`aggregations`) and also a `summary` view for that app, a `licences` view and a `security` view.
* `licences`: this is the same as `summary` but exclusively for licence violations.
* `security`: this is the same as `summary` but exclusively for security violations.

NOTE: adding the `licences` and `security` data together will not produce the overall `summary` data because there are also `quality` and `other` types of violations that are included in `summary` but not in `licences` or `security`.

### Understanding `summary`

If we go inside `summary` we can see the following:

* `appNames`: this is a list of all the application names within scope.
* `orgNames`: this is a list of all the organization names within scope. The entries match one-for-one each one of the applications, so there will be duplicate organization names.
* `weeks`: this is the range of weeks in scope, in ISO format (week number). This was selected when running the success_metrics.py script and was set by default to 6 weeks, so if we were in the middle of week 38, we would request the IQ server for weeks 32, 33, 34, 35, 36 and 37 (the past six fully completed weeks).
* `timePeriodStart`: this is a list of the weeks in scope in normal date format instead of ISO format.
* `appNumberScan`: this is a list of the number of applications that have been scanned in each of the weeks in scope. 
* `appOnboard`: this is a list of the number of applications onboarded in the IQ server in each of the weeks in scope. 
* `weeklyScans`: this is a list of the total number of scans per week in scope.
* `mttrLowThreat`: this is a list of the overall MTTR (Mean Time To Resolution) measured in days for all Low Threat vulnerabilities per week.
* `mttrModerateThreat`: this is a list of the overall MTTR (Mean Time To Resolution) measured in days for all Moderate Threat vulnerabilities per week.
* `mttrSevereThreat`: this is a list of the overall MTTR (Mean Time To Resolution) measured in days for all Severe Threat vulnerabilities per week.
* `mttrCriticalThreat`: this is a list of the overall MTTR (Mean Time To Resolution) measured in days for all Critical Threat vulnerabilities per week.
* `discoveredCounts`: this is a dictionary containing all the combined (Security, License, Quality & Other) discovered vulnerabilities for each threat level. `LIST` is the aggregation of all threat level violations where each element of the list is one of the applications in scope. `TOTAL` is a list aggregating all threat level violations for all applications in scope combined where each element of the list is one of the weeks in scope.
* `fixedCounts`: this is a dictionary containing all the combined (Security, License, Quality & Other) fixed vulnerabilities for each threat level. `LIST` is the aggregation of all threat level violations where each element of the list is one of the applications in scope. `TOTAL` is a list aggregating all threat level violations for all applications in scope combined where each element of the list is one of the weeks in scope.
* `waivedCounts`: this is a dictionary containing all the combined (Security, License, Quality & Other) waived vulnerabilities for each threat level. `LIST` is the aggregation of all threat level violations where each element of the list is one of the applications in scope. `TOTAL` is a list aggregating all threat level violations for all applications in scope combined where each element of the list is one of the weeks in scope.
* `openCountsAtTimePeriodEnd`: this is a dictionary containing all the combined (Security, License, Quality & Other) vulnerabilities for each threat level that have not yet been fixed or waived (this is the current backlog or risk exposure). `LIST` is the aggregation of all threat level violations where each element of the list is one of the applications in scope. `TOTAL` is a list aggregating all threat level violations for all applications in scope combined where each element of the list is one of the weeks in scope.
* `riskRatioCritical`: this is a list calculating the Critical risk ratio (number of Critical vulnerabilities divided by the total number of applications onboarded) for each week in scope.
* `riskRatioSevere`: this is a list calculating the Severe risk ratio (number of Severe vulnerabilities divided by the total number of applications onboarded) for each week in scope.
* `riskRatioModerate`: this is a list calculating the Moderate risk ratio (number of Critical vulnerabilities divided by the total number of applications onboarded) for each week in scope.
* `riskRatioLow`: this is a list calculating the Low risk ratio (number of Critical vulnerabilities divided by the total number of applications onboarded) for each week in scope.



### Understanding `apps`

If we go inside `apps`, we can see that first element in the list (number 0), has an `applicationId, applicationPublicId, applicationName, organizationId, organizationName` to be able to identify this particular application within a specific organization.

Then we can see the following:

* `aggregations`: this is the raw data collected by the API call. All the values inside aggregations have been explained in section 2. Explaining the Success Metrics Data API
* `summary`: this is the summary of all the outcome-based success metrics resulting from processing the raw data from the API call. More information later below.
* `licences`: this is the same as `summary` but exclusively for licence violations (for this particular app)
* `security`: this is the same as `summary` but exclusively for security violations (for this particular app)

Now it is time to explore the summary dictionary in more detail:

Below are each one of them explained:
* `weeks`: this is a list of all the weeks in ISO format that contain data. It is possible that a particular app was not scanned during one or more of the weeks in scope
* `fixedRate`: this is the YTD weekly rolling average (in percentage) of the Fixed Rate for Security/License/Quality/Other vulnerabilities combined, for all Low/Moderate/Severe/Critical threat levels combined for that particular app. fixedRate is calculated as fixedCounts / openCountsAtTimePeriodEnd (for the previous week) in percentage. For example if you fixed 5 Security Critical vulnerabilities in week 2 and at the end of week 1 you had left 50 open, the Fixed Rate would be 10%.
* `waivedRate`: this is the YTD weekly rolling average (in percentage) of the Waived Rate for Security/License/Quality/Other vulnerabilities combined, for all Low/Moderate/Severe/Critical threat levels combined for that particular app. waivedRate is calculated as waivedCounts / openCountsAtTimePeriodEnd (for the previous week) in percentage. For example if you waived 5 Security Critical vulnerabilities in week 2 and at the end of week 1 you had left 50 open, the Waived Rate would be 10%.
* `dealtRate`: this is the YTD weekly rolling average (in percentage) of the Dealt-with Rate for Security/License/Quality/Other vulnerabilities combined, for all Low/Moderate/Severe/Critical threat levels combined for that particular app. DealtRate is calculated as (fixedCounts + waivedCounts) / openCountsAtTimePeriodEnd (for the previous week) in percentage. For example if you fixed 5 and waived 15 Security Critical vulnerabilities in week 2 and at the end of week 1 you had left 100 open, the Dealt-with Rate would be 20% for Security Critical vulnerabilities.
*`FixRate`: this is the overall combined Fix rate over all the weeks in scope.
*`WaiveRate`: this is the overall combined Waive rate over all the weeks in scope.
*`DealtRate`: this is the overall combined Dealt rate over all the weeks in scope.
* `FixPercent`: this is the unitary percentage (0.5 = 50%) of all dealt-with vulnerabilities that were fixed for that particular app.
* `WaiPercent` : this is the unitary percentage (0.5 = 50%) of all dealt-with vulnerabilities that were waived for that particular app. Please note that FixPercent + WaiPercent = 1 
* `evaluationCount`: this is the number of evaluations or scans that were performed on that particular app. avg provides the overall average number of scans over the weeks in scope and rng provides the isolated scans/week.

The following metrics are dictionaries and inside them, they have the avg (average value) and rng (range, or isolated values per week of data) parameters. Some of them go into more detail, with a selection of TOTAL, SECURITY, LICENSE, QUALITY and OTHER violation types and LOW, MODERATE, SEVERE and CRITICAL threat levels.

* `mttrLowThreat`: this is the Mean Time To Resolution (measured in days instead of milliseconds) for Low threat level violations for that particular app. avg provides the overall average of the weeks in scope and rng provides the isolated MTTR values.
* `mttrModerateThreat`: this is the Mean Time To Resolution (measured in days instead of milliseconds) for Moderate threat level violations for that particular app. avg provides the overall average of the weeks in scope and rng provides the isolated MTTR values.
* `mttrSevereThreat`: this is the Mean Time To Resolution (measured in days instead of milliseconds) for Severe threat level violations for that particular app. avg provides the overall average of the weeks in scope and rng provides the isolated MTTR values.
* `mttrCriticalThreat`: this is the Mean Time To Resolution (measured in days instead of milliseconds) for Critical threat level violations for that particular app. avg provides the overall average of the weeks in scope and rng provides the isolated MTTR values.
* `discoveredCounts`: this is the number of discovered vulnerabilities of a particular type (TOTAL, SECURITY, LICENSE, QUALITY, OTHER), of a particular threat level (TOTAL, LOW, MODERATE, SEVERE, CRITICAL) for that particular app. avg provides the overall average number of vulnerabilities of that type and threat level and rng provides the isolated number per week.
* `fixedCounts`: this is the number of fixed vulnerabilities of a particular type (TOTAL, SECURITY, LICENSE, QUALITY, OTHER), of a particular threat level (TOTAL, LOW, MODERATE, SEVERE, CRITICAL) for that particular app. avg provides the overall average number of vulnerabilities of that type and threat level and rng provides the isolated number per week.
* `waivedCounts`: this is the number of waived vulnerabilities of a particular type (TOTAL, SECURITY, LICENSE, QUALITY, OTHER), of a particular threat level (TOTAL, LOW, MODERATE, SEVERE, CRITICAL) for that particular app. avg provides the overall average number of vulnerabilities of that type and threat level and rng provides the isolated number per week.
* `openCountsAtTimePeriodEnd`: this is the number of open vulnerabilities of a particular type (TOTAL, SECURITY, LICENSE, QUALITY, OTHER), of a particular threat level (TOTAL, LOW, MODERATE, SEVERE, CRITICAL) for that particular app. avg provides the overall average number of vulnerabilities of that type and threat level and rng provides the isolated number per week. Open counts accumulate from previous time periods (weeks/months) and constitute the technical debt backlog to fix/remediate. For example, if you discovered 10 Security Critical violations each week for 3 weeks (total of 30 violations) and you fixed and/or waived a total of 10 Security Critical violations at the end of those 3 weeks, the openCountAtTimePeriodEndSecurityCritical counter would show 20 (Security Critical open violations).


### Understanding `licences`

The structure is identical to `summary` with data being exclusive to licence violations.

### Understanding `security`

The structure is identical to `summary` with data being exclusive to security violations.

### Understanding the successmetrics.pdf report

TBD

## Building the Docker Image

```
docker build -t iq-success-metrics:latest .
docker run -d -p 5000:5000 iq iq-success-metrics:latest
```

<!--
Is more setup needed (running IQ server, etc) for the command below to work? Could we doc the steps?
docker run -it --rm -v `pwd`/demo:/usr/src/app/output iq-success-metrics:latest -a admin:admin123 -u http://host.docker.internal:8070
-->

To keep the docker container running after its main process finishes, instead run the container with this command:
```
docker run -dit -p 5000:5000 iq-success-metrics:latest
```
The above command should print a container id, similar to `bc1d9d006052b433761a0b03453e0f5c069bcb3ebb2af0a6d9ccbaa3278ddf83`.
You can attach to the running container using that id with a command like this:
```
docker attach bc1d9d006052b433761a0b03453e0f5c069bcb3ebb2af0a6d9ccbaa3278ddf83
```

NOTE: optionally specify ```docker build --build-arg ALT_DOCKER_REGISTRY=host.docker.internal:19443 --build-arg ALT_PYPI_REGISTRY=http://host.docker.internal:8083/nexus/repository/pypi-python.org-proxy/simple -t iq-success-metrics:latest .``` to download images from a location other than docker hub

## Using the Docker Container to run the Scripts
Once you have a docker image built, use the following command to run the success_metrics.py script and store off the successmetrics.json file (see above for more information on the success_metrics.py options)
```
docker run --name iq-success-metrics -it --rm -v  "$PWD/output:/usr/src/app/output" iq-success-metrics:latest success_metrics.py -a user:password -u IQ-Server-URL -i iq-server-app-id
```

To run the reports.py script use the following docker run command (see above for information on the reports.py options:
```
docker run --name iq-success-metrics -it --rm -v  "$PWD/output:/usr/src/app/output" iq-success-metrics:latest reports.py -a -r -l -s
```

## Contributing

If you as well want to speed up the pace of software development by working on this project, jump on in! Before you start work, create
a new issue, or comment on an existing issue, to let others know you are!

## The Fine Print

It is worth noting that this is **NOT SUPPORTED** by Sonatype, and is a contribution of ours to the open source community (read: you!)

Don't worry, using this community item does not "void your warranty". In a worst case scenario, you may be asked by the Sonatype Support team to remove the community item in order to determine the root cause of any issues.

Remember:

* Use this contribution at the risk tolerance that you have
* Do NOT file Sonatype support tickets related to iq-success-metrics
* DO file issues here on GitHub, so that the community can pitch in

Phew, that was easier than I thought. Last but not least of all:

Have fun creating and using this plugin and the Nexus platform, we are glad to have you here!

## Getting help

Looking to contribute to our code but need some help? There's a few ways to get information:

* Chat with us on [Gitter](https://gitter.im/sonatype/nexus-developers)

## Troubleshooting

### Sonatype Logo

Do not forget to download `sonatype_logo.png` together with the source code. This file is available in the release assets, but it is not automatically included in the source code .zip file.

### Windows

If you are having trouble installing pip or the Python dependencies (plotly, fpdf, requests, psutils) due to SSL error, you can use the following commands to overcome it:

To install pip:

`python -m pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org`

To install plotly (replace plotly with rest of dependencies like fpdf, requests and psutils):

`python -m pip install plotly --trusted-host pypi.org --trusted-host files.pythonhosted.org`

When you install Orca the first time in Windows, it will not work until you restart your machine.

You will need to add python, pip and orca to your Windows `PATH` for the script to work.
