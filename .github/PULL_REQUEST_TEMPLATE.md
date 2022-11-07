What:

\<For your reviewers' sake, please describe in a sentence or two what this PR is accomplishing (usually from the users' perspective, but not necessarily).\>

Why:

\<For your reviewers' sake, please describe in ~1 paragraph what the value of this PR is to our users or to ourselves.\>

How:

\<For your reviewers' sake, please describe in ~1 paragraph how this PR accomplishes its goal.\>

\<If the PR is big, please indicate where a reviewer should start reading it (i.e. which file or function).\>

---

Have you read [CONTRIBUTING.md](https://github.com/DataBiosphere/bond/blob/develop/CONTRIBUTING.md) lately? If not, do that first.

I, the developer opening this PR, do solemnly pinky swear that:

- [ ] I've followed [the instructions](https://github.com/DataBiosphere/bond/blob/develop/CONTRIBUTING.md#api-changes) if I've made any changes to the API, _especially_ if they're breaking changes

In all cases:

- [ ] Get two thumbsworth of review and PO signoff if necessary. 
- [ ] Verify all tests go green
- [ ] Squash and merge; you can delete your branch after this **unless it's for a hotfix**. In that case, don't delete it!
- [ ] Test this change deployed correctly and works on dev environment after deployment
- [ ] **Release to production** - Releasing to prod is a manual process (see [instructions to release to prod](https://github.com/DataBiosphere/bond/blob/develop/README.md#production-deployment-checklist)). Either do this now or create a ticket and schedule the release.
