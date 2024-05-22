# Setting Up Highly Available Oracle SIDB with Monitoring on Kubernetes

This comprehensive guide walks you through deploying and managing a highly available Oracle Single Instance Database (SIDB) on Kubernetes using the Oracle Database Operator (OraOperator). Additionally, you'll learn how to set up comprehensive monitoring for your database using Prometheus and Grafana.

## Table of Contents

1. Prerequisites
2. Installing OraOperator
3. Deploying the Primary SIDB
4. Deploying the Standby SIDB
5. Enabling Data Guard for High Availability
6. Setting Up Observability (Monitoring)
    * 6.1 Creating a Monitoring User in Oracle
    * 6.2 Creating the Secret for the Exporter
    * 6.3 Deploying the Exporter
    * 6.4 Configuring the Exporter
7. Installing and Configuring Prometheus
8. Installing and Configuring Grafana
9. Troubleshooting
10. Conclusion

## 1. Prerequisites

* Kubernetes cluster (e.g., Minikube, a cloud provider's cluster)
* Oracle Container Registry credentials
* SQL*Plus or another Oracle SQL client installed locally
* Helm package manager (v3 or later)

## 2. Installing OraOperator

1. **Create Namespace:**
   ```bash
   kubectl create namespace orao-ha
   ```

2. **Create Oracle Container Registry Secret:**

   ```bash
   kubectl create secret docker-registry regcred \
       --docker-server=container-registry.oracle.com \
       --docker-username=<your_username> \
       --docker-password=<your_token> \
       -n orao-ha
   ```

   * Replace placeholders with your actual Oracle credentials.

3. **Create SIDB Admin Password Secret:**

   ```bash
   kubectl create secret generic admin-password --from-literal=sidb-admin-password='<your_strong_password>' -n orao-ha
   ```

   * Replace `<your_strong_password>` with a strong password.

4. **Install Cert-manager:**

   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml
   ```

5. **Create ClusterRoleBinding:**

   ```bash
   kubectl apply -f https://raw.githubusercontent.com/oracle/oracle-database-operator/master/deploy/rbac/oracle-database-operator-clusterrolebinding.yaml
   ```

6. **Deploy OraOperator:**

   ```bash
   kubectl apply -f https://raw.githubusercontent.com/oracle/oracle-database-operator/master/deploy/crd_and_operator.yaml
   ```

7. **Verify Installation:**
   ```bash
   kubectl get pods -n oracle-database-operator-system
   ```

## 3. Deploying the Primary SIDB

1. **Install the Oracle Database Helm chart:**
    ```bash
    helm repo add oraclecharts https://oracle.github.io/charts
    helm repo update
    helm install adria-ora-sidb oraclecharts/oracle-sidb -n orao-ha -f sidb/sidb_values.yaml
    ```
    * Replace `sidb/sidb_values.yaml` with your custom `values.yaml` path, adjusting parameters as needed.

## 4. Deploying the Standby SIDB

1. **Modify `sidb_values.yaml`:**
   * Uncomment or add the configuration for the standby instance in your `sidb_values.yaml` file.
2. **Upgrade the Helm Release:**
    ```bash
    helm upgrade adria-ora-sidb oraclecharts/oracle-sidb -n orao-ha -f sidb/sidb_values.yaml
    ```

## 5. Enabling Data Guard for High Availability

1. **Modify `sidb_values.yaml`:**
   * Uncomment or add the Data Guard configuration in your `sidb_values.yaml` file.

2. **Upgrade the Helm Release:**
    ```bash
    helm upgrade adria-ora-sidb oraclecharts/oracle-sidb -n orao-ha -f sidb/sidb_values.yaml
    ```

## 6. Setting Up Observability (Monitoring)

### 6.1 Creating a Monitoring User in Oracle

1. **Port-Forward Database:** 
   ```bash
   kubectl port-forward svc/adria-ora-sidb-primary-ext -n orao-ha 1521:1521
   ```

2. **Connect to Database (SQL*Plus):**

   ```bash
   sqlplus sys/<your_password>@localhost:1521/ORCLP1 AS SYSDBA
   ```
   * replace `ORCLP1` with your PDB name

3. **Create the `c##monitor` User and Grant Privileges:**

   ```sql
   CREATE USER c##monitor IDENTIFIED BY <strong_password>;
   GRANT CREATE SESSION, SELECT ANY DICTIONARY, SELECT_CATALOG_ROLE, SELECT ON V_$DATABASE, SELECT ON V_$INSTANCE, SELECT ON V_$SYSMETRIC, SELECT ON V_$SYSSTAT, SELECT ON V_$SESSTAT, SELECT ON V_$SQLSTATS TO C##MONITOR;
   ```

4. **Commit Changes:**
   ```sql
   COMMIT;
   ```
 
### 6.2 Creating the Secret for the Exporter

```bash
kubectl create secret generic db-secret \
    --from-literal=username='c##monitor' \
    --from-literal=password='<your_password>' \
    --from-literal=connection='adria-ora-sidb-primary.orao-ha.svc.cluster.local:1521/ORCLP1' -n orao-ha
```

### 6.3 Deploying the Exporter

   ```bash
   kubectl apply -f observability/databaseobserver.yaml -n orao-ha
   ```
### 6.4 Configuring the Exporter

Update the  ```databaseobserver.yaml`` 
```yaml
  exporter:
    image: "container-registry.oracle.com/database/observability-exporter:latest [invalid URL removed]"
    configuration:
      configmap:
        key: "sample_config.toml"
        configmapName: "devcm-oradevdb-config"

    service:
      port: 9161
```

**Create ConfigMap:**

```bash
kubectl create configmap devcm-oradevdb-config --from-file=sample_config.toml -n orao-ha
```

## 7. Installing and Configuring Prometheus

1. **Install Prometheus:**
   ```bash
   helm repo add prometheus-community [https://prometheus-community.github.io/helm-charts](https://prometheus-community.github.io/helm-charts)
   helm repo update
   helm install prometheus prometheus-community/prometheus --create-namespace -n monitoring
   ```

2. **Update Prometheus Configuration (scrape_configs):**

   ```bash
   kubectl edit configmap prometheus-server -n monitoring 
   ```
   ```yaml
   - job_name: 'oracle-exporter'
     metrics_path: '/metrics'
     scrape_interval: 15s
     scrape_timeout: 10s
     static_configs:
     - targets: ['obs-svc-obs-sample.orao-ha.svc.cluster.local:9161']
   ```

3. **Restart Prometheus Pod:**

   ```bash
   kubectl delete pod <prometheus-server-pod-name> -n monitoring
   ```

## 8. Installing and Configuring Grafana

1. **Install Grafana:**
   ```bash
   helm repo add grafana [https://grafana.github.io/helm-charts](https://grafana.github.io/helm-charts)
   helm repo update
   helm install oracle-grafana grafana/grafana -n orao-ha
   ```

2. **Port-Forward Grafana (Optional):**
   ```bash
   kubectl port-forward svc/oracle-grafana -n orao-ha 3000:80 
   ```

3. **Add Prometheus Data Source in Grafana:**
    - Open Grafana (`http://localhost:3000`).
    - Go to "Configuration" -> "Data Sources".
    - Add a new Prometheus data source with URL `http://prometheus-server.monitoring:80`.


## 9. Troubleshooting

If you encounter any issues, refer to the OraOperator documentation, check the logs of the pods (`kubectl logs <pod-name> -n <namespace>`), and verify the network connectivity between components.

## 10. Conclusion

You have successfully deployed a highly available Oracle SIDB with Data Guard replication on Kubernetes using OraOperator. You've also established comprehensive monitoring using Prometheus to collect metrics and Grafana to visualize them. This setup provides a scalable and reliable foundation for running your Oracle databases in a Kubernetes environment.
