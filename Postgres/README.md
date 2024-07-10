
# Deployment of Crunchy Data PostgreSQL Operator on Kubernetes

This document provides step-by-step instructions for deploying the Crunchy Data PostgreSQL Operator on Kubernetes, configuring it using ArgoCD, and setting up monitoring with Grafana.

## Prerequisites

- A running Kubernetes cluster
- `kubectl` command-line tool configured to interact with your cluster
- `kustomize` installed
- Git repository containing the necessary manifests

## Step 1: Install Cert-Manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.1/cert-manager.yaml
```

## Step 2: Install ArgoCD

If ArgoCD is not installed, follow these steps:

```bash
# Create namespace for ArgoCD
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### Access ArgoCD UI

To access the ArgoCD UI, run:

```bash
kubectl get svc -n argocd
kubectl port-forward svc/argocd-server 8080:443 -n argocd
```

### Login to ArgoCD

Get the initial admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 --decode && echo
```

Login to the ArgoCD UI using the admin user and the password obtained above. You can change and delete the initial password as needed.

## Step 3: Add Cert-Manager Application to ArgoCD

Login to ArgoCD and create a new application named `certman`:

1. Select `Kustomize`.
2. Add the path from the repository: `/Postgres/certmanager/certman`.
3. Create the application (the TLS certs issuer is Kubernetes cert-manager).

## Step 4: Deploy Crunchy PostgreSQL Operator CRDs

First, deploy the namespace:

```bash
kubectl apply -k Postgres/Postgres-cluster-deployement/install/namespace
```

Then, deploy the CRDs:

```bash
kustomize build Postgres/Postgres-cluster-deployement/install/default | kubectl apply --server-side -f -
```

## Step 5: Create PostgreSQL Cluster Application in ArgoCD

Create a new application in ArgoCD named `postgres-cluster`:

1. Select `Kustomize`.
2. Add the path: `/Postgres/Postgres-cluster-deployement/postgres-cluster`.
3. Deploy the application (pgpool included).

## Step 6: Deploy PgBouncer

Add the helm repository:

 repo : medxps https://medxps.github.io/helm-charts/


Create a new application in ArgoCD named `pgbouncer`:

1. Select `Helm`.
2. Use the repository: `https://medxps.github.io/helm-charts/`.
3. Ensure the target version is `2.4.0` or check for updates at `https://github.com/medXPS/helm-charts/blob/main/stable/pgbouncer/Chart.yaml`.

You can enable observability and add Grafana dashboards.

## Step 7: Deploy Monitoring Pack for PGO

Create a new application in ArgoCD named `postgres-monitoring`:

1. Select `Kustomize`.
2. Add the path: `/Postgres/Postgres-cluster-deployement/monitoring`.
3. Deploy the application.

## Step 8: Access Grafana Dashboards

Port forward Grafana to access it:

```bash
kubectl port-forward svc/crunchy-grafana 3000:80 -n monitoring
```

Navigate to `http://localhost:3000` and log in to Grafana. Select customized dashboards from `/Postgres/Postgres-cluster-deployement/monitoring/custom-grafana-dash`.

## Step 9: Connect Your Java Application

You can expose the PgBouncer port or add a LoadBalancer layer to link your Java application with the PostgreSQL cluster.
## Step 10: Setting Up pgAdmin for PostgreSQL on Kubernetes

This guide outlines the steps to set up pgAdmin to manage PostgreSQL databases deployed on Kubernetes using the Crunchy Data PostgreSQL Operator.



### 1. Create pgAdmin Admin User Secret

To create an admin user in pgAdmin, follow these steps to set up a Kubernetes secret that stores the admin user's password.

```sh
kubectl create secret generic pgadmin-password-secret \
  --from-literal=adria-dba-password=adria-dba-admin-2024 \
  -n pgo-ha
  ```

  
### 2. Deploy pgAdmin with Admin User and Server Discovery
Deploy pgAdmin with an admin user and configure it to discover servers from your PostgreSQL clusters using 

```yaml
  serverGroups:
  - name: name-discovery
    postgresClusterName: adria-pg-db
      
  ```

### 3. . Access pgAdmin Interface
Once deployed, access the pgAdmin web interface using port forwarding:

```sh
  kubectl port-forward pod/pgadmin-pod-name -n pgo-ha 5050:5050

  ```

## Conclusion

By following these steps, you have successfully deployed the Crunchy Data PostgreSQL Operator on Kubernetes, configured it using ArgoCD, and set up monitoring with Grafana.
```
