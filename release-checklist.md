--- Production Deployment Preparation
* [] Confirm that `dev_tests_passed_[timestamp]` tag was created for the commit you wish to deploy.
>> When the latest code passes tests in GHA, it is tagged `dev_tests_passed_[timestamp]` where `[timestamp]` is the epoch time when the tag was created.
* [] Update the ticket name, replacing `x.x.x` with the semver number.
* [] Create Bond Release in Jira
>> In Jira, make sure the Bond Release exists or create a new one in the [Cloud Integration Project](https://broadworkbench.atlassian.net/projects/CA?selectedItem=com.atlassian.jira.jira-projects-plugin%3Arelease-page) named like: `Bond-X.Y.Z` where `X.Y.Z` is the same semantic version number you created in the previous step
* [] Set the `Fix Version` for each Jira Issue included in this release
>> Find the tickets included in this release by looking through the commits/PRs committed to the main branch since the last release.
>> 
>> Set the `Fix Version` field to the release name you created in the previous step.  The status of each of these issues should be: `Merged to Dev`.  If the status is something else, verify whether the ticket should be included in this release. Each Jira issue must have a clear description of the change and its security impact.
* [] Set the `Fix Version` on _this_ Release Issue 
--- Deploy and Test
* [] Deploy to `dev` and perform manual test
>> * Bond is automatically deployed to dev on merge to the default branch (i.e. `develop`).
>> * Perform the [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#)
If desired, you can manually promote Bond through to whatever environments you want as follows, however, new Bond helm charts and versions are automatically released on merge to Bond and terra-helmfile and promoted with the monolith release, so this is for independent releases or hotfixes only:
* [] Check the [Release Protection Window Calendar](https://calendar.google.com/calendar/u/0?cid=YnJvYWRpbnN0aXR1dGUub3JnX2ZrMGMxb2E0Ym5rY21rOXEyajY5ZWdtMjljQGdyb3VwLmNhbGVuZGFyLmdvb2dsZS5jb20)
* [] Notify the [#workbench-release](https://broadinstitute.slack.com/archives/C6DTFUCDD) Slack channel that you will be releasing a new version of Bond to `staging`, and `prod` along with the link to the release version in Jira.
* [] Deploy to `staging` and perform manual test
>> * Navigate to [bond-staging in Beehive](https://beehive.dsp-devops.broadinstitute.org/environments/staging/chart-releases/bond), click on "Change Versions" and then "Click to Refresh and Preview Changes". Review the changeset, and if it looks good, apply it and wait for Staging to be updated.
>> * Perform the [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#)
* [] Deploy to `prod` and perform manual test
>> * In order to deploy to `prod`, you must be on the DSP Suitability Roster.
>> * Navigate to [bond-bond in Beehive](https://beehive.dsp-devops.broadinstitute.org/environments/prod/chart-releases/bond), click on "Change Versions" and then "Click to Refresh and Preview Changes". Review the changeset, and if it looks good, apply it and wait for Prod to be updated.
>> * Perform the [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#)
* [] Transition all tickets in the Release in Jira to "Done"
* [] Mark the Release in Jira as "Released"
>> Navigate to the [Releases Page](https://broadworkbench.atlassian.net/projects/CA?selectedItem=com.atlassian.jira.jira-projects-plugin%3Arelease-page) in Jira and mark the version as "Released"
