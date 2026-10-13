// Real Ansible validation runs on the dedicated Jenkins Agent.
// This pipeline does NOT deploy infrastructure or access GCP/AAP.
pipeline {
    agent {
        label 'jenkins-agent'
    }

    options {
        skipDefaultCheckout(true)
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify Toolchain') {
            steps {
                sh '''
                    python --version
                    ansible-playbook --version
                    ansible-lint --version
                    yamllint --version
                '''
            }
        }

        stage('YAML Lint') {
            steps {
                sh 'yamllint .yamllint playbooks/validate_local.yml'
            }
        }

        stage('Ansible Lint') {
            steps {
                sh 'ansible-lint playbooks/validate_local.yml'
            }
        }

        stage('Ansible Syntax Check') {
            steps {
                sh 'ansible-playbook -i localhost, --syntax-check playbooks/validate_local.yml'
            }
        }

        stage('Ansible Local Execution') {
            steps {
                sh 'ansible-playbook -i localhost, -c local playbooks/validate_local.yml'
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: Ansible YAML, lint, syntax, and local execution checks passed.'
        }
        failure {
            echo 'FAILED: Review the console log to identify the validation error.'
        }
    }
}
