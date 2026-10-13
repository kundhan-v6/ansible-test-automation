// Verify that Jenkins executes pipeline steps on the dedicated build agent.
// This pipeline only checks agent connectivity; it does not access GCP or AAP.
pipeline {
    agent {
        label 'jenkins-agent'
    }

    options {
        skipDefaultCheckout(true)
        timestamps()
    }

    stages {
        stage('Checkout from GitHub') {
            steps {
                checkout scm
                echo 'Repository checkout completed on Jenkins Agent.'
            }
        }

        stage('Verify Agent') {
            steps {
                sh '''
                    echo "Hostname:"
                    hostname
                    echo "Current user:"
                    whoami
                    echo "Working directory:"
                    pwd
                '''
            }
        }

        stage('Verify Repository') {
            steps {
                script {
                    if (!fileExists('README.md')) {
                        error('README.md is missing from the checked-out repository.')
                    }
                }
                echo 'Repository verified on Jenkins Agent.'
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: GitHub-backed pipeline executed on dedicated Jenkins Agent.'
        }
        failure {
            echo 'FAILED: Review agent tools, connectivity, or console logs.'
        }
    }
}
