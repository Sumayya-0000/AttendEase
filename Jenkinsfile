pipeline {
  agent any
  triggers { githubPush() }
  environment {
    IMAGE_NAME = 'DOCKERHUB_USER/attendance-tracker'
    K8S_NAMESPACE = 'default'
  }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Test') {
      steps {
        sh 'python3 -m venv .venv-ci || true'
        sh '. .venv-ci/bin/activate && pip install -r requirements.txt && pytest -q'
      }
    }
    stage('Build Image') {
      steps {
        sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} -t ${IMAGE_NAME}:latest .'
      }
    }
    stage('Push Image') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_TOKEN')]) {
          sh '''echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USER" --password-stdin
          docker push ${IMAGE_NAME}:${BUILD_NUMBER}
          docker push ${IMAGE_NAME}:latest
          docker logout'''
        }
      }
    }
    stage('Deploy to Kubernetes') {
      steps {
        withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG_FILE')]) {
          sh '''export KUBECONFIG="$KUBECONFIG_FILE"
          sed "s|DOCKERHUB_USER/attendance-tracker:latest|${IMAGE_NAME}:${BUILD_NUMBER}|g" k8s/deployment.yaml | kubectl apply -f -
          kubectl apply -f k8s/pvc.yaml
          kubectl apply -f k8s/service.yaml
          kubectl rollout status deployment/attendance-tracker --timeout=180s'''
        }
      }
    }
  }
  post { always { cleanWs() } }
}
