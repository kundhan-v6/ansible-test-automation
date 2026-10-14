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
        CONFIG_FILE = 'inventories/dev/group_vars/all.yml'
        DEPLOY_PLAYBOOK = 'playbooks/deploy_infrastructure.yml'
        STATE_SCRIPT = 'scripts/network_state.py'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Validate') {
            steps {
                sh '''
                    set -eu

                    export ANSIBLE_CONFIG="$PWD/ansible.cfg"

                    "$ANSIBLE_BIN/yamllint" \
                        "$CONFIG_FILE" \
                        roles/gcp_network/defaults/main.yml \
                        roles/gcp_network/tasks/main.yml \
                        "$DEPLOY_PLAYBOOK"

                    "$ANSIBLE_BIN/ansible-lint" \
                        "$DEPLOY_PLAYBOOK"

                    "$ANSIBLE_BIN/ansible-playbook" \
                        -i localhost, \
                        "$DEPLOY_PLAYBOOK" \
                        --syntax-check

                    "$ANSIBLE_BIN/python" -m py_compile \
                        "$STATE_SCRIPT"

                    echo "SUCCESS: Code validation passed."
                '''
            }
        }

        stage('Verify Authentication') {
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

                        "$ANSIBLE_BIN/python" -c '
import os
import google.auth
from google.auth.transport.requests import Request

credentials, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

actual = getattr(
    credentials,
    "service_account_email",
    None
)

expected = os.environ["EXPECTED_SERVICE_ACCOUNT"]

if actual != expected:
    raise SystemExit("Unexpected GCP identity")

credentials.refresh(Request())

print("SUCCESS: GCP authentication verified")
print("Identity:", actual)
'
                    '''
                }
            }
        }

        stage('Plan / Preview') {
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

                        "$ANSIBLE_BIN/python" \
                            "$STATE_SCRIPT" preview
                    '''
                }
            }
        }

        stage('Approval') {
            steps {
                timeout(time: 15, unit: 'MINUTES') {
                    input(
                        message: 'Review the networking preview. Approve deployment to ansible-test-automation?',
                        ok: 'Deploy Infrastructure'
                    )
                }
            }
        }

        stage('Deploy') {
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

                        export ANSIBLE_CONFIG="$PWD/ansible.cfg"
                        export SSL_CERT_FILE="$("$ANSIBLE_BIN/python" -m certifi)"

                        "$ANSIBLE_BIN/ansible-playbook" \
                            -i localhost, \
                            "$DEPLOY_PLAYBOOK"
                    '''
                }
            }
        }

        stage('Verify') {
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

                        "$ANSIBLE_BIN/python" \
                            "$STATE_SCRIPT" verify
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'network-plan.json',
                allowEmptyArchive: true
            )
        }

        success {
            echo 'SUCCESS: Infrastructure deployment verified.'
        }

        failure {
            echo 'FAILED: Review Jenkins console output.'
        }

        aborted {
            echo 'ABORTED: Deployment cancelled or approval expired.'
        }
    }
}
