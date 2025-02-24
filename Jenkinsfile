pipeline {
    agent any
    parameters {
        string(name: 'FAILED_JOB_NAME', defaultValue: '', description: '')
        string(name: 'FAILED_BUILD_NUMBER', defaultValue: '', description: '')
    }
    stages {
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t analyze-log-image .'
            }
        }
        stage('Analyze log') {
            steps {
                withCredentials([
                    string(credentialsId: 'jenkins-api-token', variable: 'JENKINS_API_TOKEN')
                ]) {
                    sh '''
                        docker run --rm \
                        -e JENKINS_API_TOKEN=${JENKINS_API_TOKEN} \
                        -e FAILED_JOB_NAME=${FAILED_JOB_NAME} \
                        -e FAILED_BUILD_NUMBER=${FAILED_BUILD_NUMBER} \
                        -e LLM_API_URL="http://llm-api-container:8000/predict" \
                        --network llm-net \
                        analyze-log-image > analysis_report.txt
                    '''
                }
            }
        }
    }
}
