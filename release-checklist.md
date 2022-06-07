--- Production Deployment Preparation
* [] Confirm that `dev_tests_passed_[timestamp]` tag was created for the commit you wish to deploy.
>> When the latest code passes tests in CircleCI, it is tagged `dev_tests_passed_[timestamp]` where `[timestamp]` is the epoch time when the tag was created.
* [] Create and push a new [semver](https://semver.org/) tag for this same commit.
>> You should look at the existing tags to ensure that the tag is incremented properly based on the last released version.  Tags should be plain semver numbers like `1.0.0` and should not have any additional prefix like `v1.0.0` or `releases/1.0.0`.  Suffixes are permitted so long as they conform to the [semver spec](https://semver.org/).
* [] Manually tag the Docker image with the correct semver number on Quay
>> Pushing the new tag to the git origin repository will _not_ automatically tag the Docker image.  You will need to manually tag the Docker image with the correct semver number.  Go to the [Bond project on Quay.io](https://quay.io/repository/databiosphere/bond?tab=tags) and navigate to the "Tags" menu.  You should see two new images for `latest` and `develop`.  Confirm that the ages of these images correspond to when you merged your changes into the `develop` branch.  On the right of one of these rows, click on the gear icon and select "Add New Tag".  Enter the semver number for your release.
>> 
>> NOTE: if you have issues logging in, you may need to link your old Quay account with new redhat account at https://recovery.quay.io/
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
>> * Navigate to the [Bond Manual Deploy](https://fc-jenkins.dsp-techops.broadinstitute.org/view/Indie%20Deploys/job/bond-manual-deploy/) job and click the "Build with Parameters" link.  Select the `TAG` that you just created during the preparation steps and `dev` as the Target tier to deploy to.
>> * Technically, this same commit is probably already running on `dev` courtesy of the automatic `dev` deployment job. However, deploying again is an important step because someone else may have triggered a `dev` deployment and we want to ensure that you understand the deployment process, the deployment tools are working properly, and that everything is working as intended.
>> * Perform the [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#)
* [] Check the [Release Protection Window Calendar](https://calendar.google.com/calendar/u/0?cid=YnJvYWRpbnN0aXR1dGUub3JnX2ZrMGMxb2E0Ym5rY21rOXEyajY5ZWdtMjljQGdyb3VwLmNhbGVuZGFyLmdvb2dsZS5jb20)
* [] Notify the [#workbench-release](https://broadinstitute.slack.com/archives/C6DTFUCDD) Slack channel that you will be releasing a new version of Bond to `alpha`, `staging`, and `prod` along with the link to the release version in Jira.
* [] Deploy to `alpha` and perform manual test
>> * Navigate to the [Bond Manual Deploy](https://fc-jenkins.dsp-techops.broadinstitute.org/view/Indie%20Deploys/job/bond-manual-deploy/) job and click the "Build with Parameters" link.  Select the `TAG` that you just created during the preparation steps and `alpha` as the Target tier to deploy to.
>> * Perform the [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#)
* [] Deploy to `staging` and perform manual test
>> * Navigate to the [Bond Manual Deploy](https://fc-jenkins.dsp-techops.broadinstitute.org/view/Indie%20Deploys/job/bond-manual-deploy/) job and click the "Build with Parameters" link.  Select the `TAG` that you just created during the preparation steps and `staging` as the Target tier to deploy to.
>> * Perform the [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#)
* [] Deploy to `prod` and perform manual test
>> * In order to deploy to `prod`, you must be on the DSP Suitability Roster.  You will need to log into the production Jenkins instance and use the "Bond Manual Deploy" job to release the same tag to production.
>> * Perform the [manual test](https://docs.google.com/document/d/1-SXw-tgt1tb3FEuNCGHWIZJ304POmfz5ragpphlq2Ng/edit?ts=5e964fbe#)
* [] Transition all tickets in the Release in Jira to "Done"
* [] Mark the Release in Jira as "Released"
>> Navigate to the [Releases Page](https://broadworkbench.atlassian.net/projects/CA?selectedItem=com.atlassian.jira.jira-projects-plugin%3Arelease-page) in Jira and mark the version as "Released"
