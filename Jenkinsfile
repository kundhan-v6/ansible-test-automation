// First GitHub-backed Jenkins pipeline for the Ansible automation lab.
// This stage tests SCM connectivity only; it does not provision infrastructure.
pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
    }

    stages {
        stage('Checkout from GitHub') {
            steps {
                checkout scm
                echo 'Repository checkout completed.'
            }
        }

        stage('Verify repository') {
            steps {
                script {
                    if (!fileExists('README.md')) {
                        error('README.md is missing from the checked-out repository.')
                    }
                }
                echo 'README.md exists in the Jenkins workspace.'
            }
        }

        stage('Prepare Ansible validation') {
            steps {
                echo 'SCM integration works. Real Ansible lint and tests will be added using a dedicated build agent.'
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: Jenkins loaded its Jenkinsfile from GitHub and checked out the repository.'
        }
        failure {
            echo 'FAILED: Inspect checkout or pipeline configuration in the Jenkins console.'
        }
    }
}
