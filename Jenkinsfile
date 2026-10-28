
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'AttendEase source code checked out from GitHub'
                bat 'git --version'
            }
        }

        stage('Test') {
            steps {
                echo 'Installing Python dependencies and running tests'
                bat 'python --version'
                bat 'python -m pip install -r requirements.txt'
                bat 'python -m compileall -q app.py'
                bat 'python -m pytest tests -v'
            }
        }

        stage('Build Image') {
            steps {
                echo 'Building AttendEase Docker image'
                bat 'docker --version'
                bat 'docker build -t attendease:latest .'
            }
        }
    }

    post {
        success {
            echo 'AttendEase pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the Console Output.'
        }
    }
}
