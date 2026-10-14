
pipeline {
    agent {
        label 'jenkins-agent'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    environment {
        GCP_PROJECT = 'ansible-test-automation'
        EXPECTED_SERVICE_ACCOUNT = 'dev-infra-automation@ansible-test-automation.iam.gserviceaccount.com'
        ANSIBLE_BIN = '/opt/ci-venv/bin'
        VPC_PLAYBOOK = 'playbooks/infrastructure/create_vpc.yml'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Validate Ansible Code') {
            steps {
                sh '''
                    set -eu

                    echo "Validating VPC playbook..."

                    "$ANSIBLE_BIN/yamllint" "$VPC_PLAYBOOK"

                    "$ANSIBLE_BIN/ansible-lint" "$VPC_PLAYBOOK"

                    "$ANSIBLE_BIN/ansible-playbook" \
                        -i localhost, \
                        "$VPC_PLAYBOOK" \
                        --syntax-check

                    echo "Ansible validation passed."
                '''
            }
        }

        stage('Verify Jenkins GCP Authentication') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'gcp-infra-sa-json',
                        variable: 'GOOGLE_APPLICATION_CREDENTIALS'
                    )
                ]) {
                    sh '''
                        set +x
                        set -eu

                        export SSL_CERT_FILE="$("$ANSIBLE_BIN/python" -m certifi)"

                        "$ANSIBLE_BIN/python" - <<'PY'
import os
import google.auth
from google.auth.transport.requests import Request

credentials, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

expected = os.environ["EXPECTED_SERVICE_ACCOUNT"]
actual = getattr(credentials, "service_account_email", None)

if actual != expected:
    raise SystemExit(
        "ERROR: Jenkins is using an unexpected GCP service account."
    )

credentials.refresh(Request())

print("SUCCESS: Jenkins authenticated to Google Cloud.")
print("Authenticated service account:", actual)
PY
                    '''
                }
            }
        }

        stage('Approval') {
            steps {
                timeout(time: 15, unit: 'MINUTES') {
                    input(
                        message: 'Approve creation of dev-vpc in ansible-test-automation?',
                        ok: 'Deploy VPC'
                    )
                }
            }
        }

        stage('Deploy VPC Using Ansible') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'gcp-infra-sa-json',
                        variable: 'GOOGLE_APPLICATION_CREDENTIALS'
                    )
                ]) {
                    sh '''
                        set +x
                        set -eu

                        unset GCP_ACCESS_TOKEN GCP_AUTH_KIND

                        export SSL_CERT_FILE="$("$ANSIBLE_BIN/python" -m certifi)"

                        echo "Deploying dev-vpc using Ansible..."

                        "$ANSIBLE_BIN/ansible-playbook" \
                            -i localhost, \
                            "$VPC_PLAYBOOK"

                        echo "Ansible VPC deployment completed."
                    '''
                }
            }
        }

        stage('Verify VPC in GCP') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'gcp-infra-sa-json',
                        variable: 'GOOGLE_APPLICATION_CREDENTIALS'
                    )
                ]) {
                    sh '''
                        set +x
                        set -eu

                        export SSL_CERT_FILE="$("$ANSIBLE_BIN/python" -m certifi)"

                        "$ANSIBLE_BIN/python" - <<'PY'
import os
import google.auth
from google.auth.transport.requests import AuthorizedSession

project = os.environ["GCP_PROJECT"]

credentials, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

session = AuthorizedSession(credentials)

url = (
    f"https://compute.googleapis.com/compute/v1/projects/"
    f"{project}/global/networks/dev-vpc"
)

response = session.get(url, timeout=30)
response.raise_for_status()

network = response.json()

if network.get("name") != "dev-vpc":
    raise SystemExit("ERROR: VPC name does not match.")

if network.get("autoCreateSubnetworks") is not False:
    raise SystemExit("ERROR: Automatic subnet creation is enabled.")

if network.get("routingConfig", {}).get("routingMode") != "REGIONAL":
    raise SystemExit("ERROR: VPC routing mode is incorrect.")

print("SUCCESS: dev-vpc exists in GCP.")
print("VPC name:", network["name"])
print("Auto-create subnets:", network["autoCreateSubnetworks"])
print("Routing mode:", network["routingConfig"]["routingMode"])
PY
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: Jenkins Ansible VPC deployment and verification completed.'
        }

        failure {
            echo 'FAILED: Review the failed Jenkins pipeline stage.'
        }

        aborted {
            echo 'ABORTED: Deployment was cancelled or approval timed out.'
        }
    }
}
