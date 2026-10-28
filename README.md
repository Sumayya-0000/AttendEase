# Attendance Tracker — Flask + Docker + Kubernetes + Jenkins

A small attendance management app with four pages: Dashboard, Mark Attendance, Students, and Reports. SQLite stores students and daily attendance; `/health` is provided for container and Kubernetes probes.

## 1. Run locally (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python app.py
```

Open http://127.0.0.1:5000. To use port 5005: `flask --app app run --port 5005`.

## 2. Docker

```bash
docker build -t attendance-tracker:1.0 .
docker run -d --name attendance-app -p 5005:5000 -v attendance-data:/data attendance-tracker:1.0
curl http://localhost:5005/health
docker logs attendance-app
```

## 3. GitHub

Create an empty repository, then:

```bash
git init
git add .
git commit -m "Add Attendance Tracker CI/CD project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/attendance-tracker.git
git push -u origin main
```

## 4. Local Kubernetes with Minikube

The Kubernetes deployment manifest is intended for a registry image. For a local-only test, update `k8s/deployment.yaml` to use `attendance-tracker:1.0` and set `imagePullPolicy: IfNotPresent`, then run `minikube image load attendance-tracker:1.0` after building the image. Apply manifests:

```bash
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl rollout status deployment/attendance-tracker
kubectl get pods,svc
minikube service attendance-tracker --url
```

For registry deployment, replace `DOCKERHUB_USER` with your Docker Hub username and push the image first.

## 5. Jenkins CI/CD

1. Ensure the Jenkins agent has Git, Python 3, Docker CLI/daemon access, kubectl, and access to your Kubernetes cluster.
2. Replace `DOCKERHUB_USER` in `Jenkinsfile` with your Docker Hub username.
3. Add Jenkins credentials: `dockerhub-creds` (Username with password; password should be a Docker Hub access token) and `kubeconfig` (Secret file).
4. Create a Pipeline job using **Pipeline script from SCM**, Git, your repository URL, branch `main`, and script path `Jenkinsfile`.
5. Configure a GitHub webhook pointing to `https://YOUR_REACHABLE_JENKINS_URL/github-webhook/`. A localhost-only Jenkins server is not reachable by GitHub; use a properly secured public endpoint/tunnel or configure SCM polling.

The pipeline tests the app, builds and pushes an image tagged with the Jenkins build number and `latest`, applies Kubernetes resources, and waits for rollout. The Jenkins agent needs permissions to build/push images and deploy to the cluster.

## Notes

- This is a student demo, not a hardened production application. Add authentication and CSRF protection before public deployment.
- The SQLite database uses a persistent volume at `/data` in Docker/Kubernetes. For Kubernetes, the PVC's storage class must be supported by the cluster.
- Do not commit tokens, kubeconfig files, or secrets.
