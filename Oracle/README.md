

# Enabling Oracle Single Instance Database High Availability with OraOperator

This comprehensive guide walks you through deploying a highly available Oracle Single Instance Database (SIDB) on a Kubernetes cluster using OraOperator. We'll cover the installation of OraOperator, step-by-step deployment of the primary and standby SIDB instances, establishing Data Guard for synchronous replication, and configuring comprehensive observability with Prometheus and Grafana.

## Part 1: Installing the OraOperator

### Prerequisites

- A running Kubernetes cluster (such as minikube, Kind, or a cloud-based cluster)
- `kubectl` command-line tool installed and configured
- Valid credentials (username and password or auth token) for the Oracle Container Registry
- `helm` package manager for Kubernetes

### Steps

1. **Create the Namespace and Secrets:**

   - Create a dedicated namespace for your Oracle deployment:

     ```bash
     kubectl create ns orao-ha
     ```

   - Create a secret for your Oracle Container Registry credentials:

     ```bash
     kubectl create secret docker-registry regcred \
       --docker-server=container-registry.oracle.com \
       --docker-username=<your_username> \
       --docker-password=<your_token> \
       -n orao-ha
     ```

   - Create a secret for the SIDB administrator password:

     ```bash
     kubectl create secret generic admin-password \
       --from-literal=sidb-admin-password='<your_strong_password>' \
       -n orao-ha
     ```

2. **Install Cert-Manager:**

   - OraOperator uses webhooks, which require TLS certificates. Install cert-manager to manage these certificates:

     ```bash
     kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml
     ```

3. **Create Role Bindings (Cluster-Scoped Deployment):**

   - OraOperator can be deployed in cluster-scoped mode. Apply the necessary role bindings:

     ```bash
     kubectl apply -f Oracle/cluster-role-binding.yaml
     ```

4. **Deploy OraOperator:**

   - Deploy the OraOperator using the provided manifest file:

     ```bash
     kubectl apply -f oracle-database-operator.yaml
     ```

5. **Verify Installation:**

   - Check that the OraOperator pods are running:

     ```bash
     kubectl get pods -n oracle-database-operator-system
     ```

     You should see the OraOperator controller manager pods in a `Running` state.

## Part 2: Deploying the Primary SIDB

1. **Install ArgoCD (If Not Deployed):**
   - If you don't have ArgoCD installed, set it up:
     ```bash
     kubectl create namespace argocd
     kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
     ```
     - Get the ArgoCD UI URL:
       ```bash
       kubectl get svc -n argocd
       ```
       - Access the ArgoCD UI:
         ```bash
         kubectl port-forward svc/argocd-server 8080:443 -n argocd
         ```
   - Retrieve the initial admin password:
     ```bash
     kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 --decode && echo
     ```


2. **Create ArgoCD Repository:**
   - In the ArgoCD UI, create a new repository pointing to your Git repository that contains your Oracle database manifests. Test the connection to ensure it's successful.

3. **Create ArgoCD Application:**
   - Create a new ArgoCD application to manage the deployment of your Oracle SIDB.
   - Configure the application to use the Kustomize tool.

4. **Configure Kustomization:**
   - Modify the `kustomization.yaml` file to include the resources you want to deploy. Initially, only the primary SIDB should be included:

     ```yaml
     resources:
       - sidb/singleinstancedatabase.yaml
     ```

5. **Deploy the Primary SIDB:**
   - Commit and push your changes to the Git repository. ArgoCD will automatically synchronize and deploy the primary SIDB.

## Part 3: Deploying the Standby SIDB and Enabling Data Guard

1. **Modify Kustomization for Standby:**
   - Edit the `kustomization.yaml` file to include the standby SIDB:

     ```yaml
     resources:
       - sidb/singleinstancedatabase.yaml
       - sidb/singleinstancedatabase_standby.yaml
     ```

2. **Deploy the Standby SIDB:**
   - Commit and push your changes. ArgoCD will deploy the standby SIDB.

3. **Enable Data Guard (Synchronous Replication):**
   - Modify the `kustomization.yaml` file to include the Data Guard broker:

     ```yaml
     resources:
       - sidb/singleinstancedatabase.yaml
       - sidb/singleinstancedatabase_standby.yaml
       - sidb/dataguardbroker.yaml
     ```

   - Commit and push your changes. ArgoCD will configure Data Guard and establish synchronous replication. 

## Part 4: Observability with Prometheus and Grafana

1. **Create Monitoring User and Secret:**
   - Connect to the primary SIDB's PDB and create a user named `c##monitor` with the necessary privileges (e.g., `CREATE SESSION`, `SELECT ANY DICTIONARY`, `SELECT_CATALOG_ROLE`).

   ```CREATE USER c##monitor IDENTIFIED BY '<your_strong_password>';
      GRANT CREATE SESSION TO c##monitor;
      GRANT SELECT ANY DICTIONARY TO c##monitor;
      GRANT SELECT_CATALOG_ROLE TO c##monitor;
``
   - Create a Kubernetes secret `db-secret` containing the monitoring user's credentials.
  
   ``` 
   kubectl create secret generic db-secret \
  --from-literal=username='c##monitor' \
  --from-literal=password='<your_strong_password>' \
  --from-literal=connection='adria-ora-sidb-primary/ORCLP1' -n orao-ha
```

2. **Deploy Observability Exporter:**
   - Uncomment the following line in your `kustomization.yaml` file:
     ```yaml
     - observability/databaseobserver.yaml
     ```

3. **Install Prometheus and Grafana with Helm:**
   - Deploy Prometheus and Grafana using Helm charts:

     ```bash
     helm install prometheus prometheus-community/prometheus -n orao-ha
     helm install grafana grafana/grafana -n orao-ha
     ```

4. **Configure Prometheus Scraper:**
   - Edit the Prometheus `prometheus-server` ConfigMap and add a scraper configuration to target the Oracle exporter:
     ```yaml
     scrape_configs:
       - job_name: 'oracle-exporter'
         metrics_path: '/metrics'
         scrape_interval: 15s
         scrape_timeout: 10s
         static_configs:
           - targets: ['obs-svc-obs-sample.orao-ha.svc.cluster.local:9161'] 
     ```

5. **Restart Prometheus:**
   - Delete the Prometheus pod to trigger a restart with the new configuration.

6. **Verify and Access Grafana:**
   - Port-forward Grafana to your local machine:
     ```bash
     kubectl port-forward <grafana-pod-name> 3000:3000 -n orao-ha
     ```
   - Access Grafana at `http://localhost:3000` using the admin credentials (retrieved from the `grafana` secret).
   - Create a data source pointing to your Prometheus instance (`http://prometheus-service:80`).
   - Import the provided Grafana dashboard located at `/Oracle/observability/grafana/<dashboard_name>.json`.
   - Customize the dashboard and metrics as needed.

## Additional Notes

- Fine-tune the metrics collected by modifying the `sample_config.toml` file.
- Regular backups are crucial for data protection.
- Secure your database and Kubernetes cluster with appropriate measures (network policies, authentication, etc.).

Let me know if you have any other questions or modifications.
