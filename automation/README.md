# Bond Automation Tests

Before running the tests, you will need to run some variety of the following command:

`docker run --rm -e VAULT_TOKEN=$(cat ~/.vault-token) broadinstitute/dsde-toolbox vault read --format=json "secret/dsde/firecloud/dev/common/firecloud-account.json" | jq '.data' > automation/firecloud-account.json`

To run the tests from the Bond root directory:

`python -m unittest discover -s ./automation/tests -p "*_test.py"`

You can optionally specify the environment variable, `BOND_BASE_URL` to specify the host you want to test against.  This
variable will default to `https://bond-fiab.dsde-dev.broadinstitute.org:31443` unless otherwise specified. For example:

`BOND_BASE_URL="localhost:8080" python -m unittest discover -s ./automation/tests -p "*_test.py"`
