# ora-operator-
#create Nexus credentials secret 
kubectl create secret generic regcred --from-file=.dockerconfigjson=$HOME/.docker/config.json  --type=kubernetes.io/dockerconfigjson -n orao-ha
# Create  SIDB credentials secret 
kubectl create secret generic admin-password --from-literal=sidb-admin-password='Kube#adria#2024' -n orao-ha

-----
Monittoring : 
---Kubernetes
-git repo :https://github.com/oracle/oracle-db-appdev-monitoring
1)*Create a config map for you metrics definition file (optional)*

CMD: kubectl create cm db-metrics-txeventq-exporter-config --from-file=txeventq-metrics.toml -n orao-ha

2) Deploy the Oracle Database Observability exporter

CMD : < kubectl apply -f metrics-exporter-deployment.yaml -n orao-ha>

```## Copyright (c) 2021, 2023, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-exporter
  namespace: ora-ha      #check it for Kustomize 
spec:
  replicas: 1
  selector:
    matchLabels:
      app: metrics-exporter
  template:
    metadata:
      labels:
        app: metrics-exporter
    spec:
      containers:
      - name: metrics-exporter
        image: container-registry.oracle.com/database/observability-exporter:1.0.0
        imagePullPolicy: Always
        env:
          # uncomment and customize the next item if you want to provide custom metrics definitions
          #- name: CUSTOM_METRICS
          #  value: /oracle/observability/txeventq-metrics.toml
          - name: TNS_ADMIN
            value: "/oracle/tns_admin"
          - name: DB_USERNAME
            valueFrom:
              secretKeyRef:
                name: db-secret   #specify secret used  to store USERNAME of the PDB
                key: username
                optional: false
          - name: DB_PASSWORD
            valueFrom:
              secretKeyRef:
                name: db-secret  #specify secret used  to store PASSWORD of the PDB
                key: password
                optional: false
          # update the connect string below for your database - can be simple format, or use a tns name as shown:
          - name: DB_CONNECT_STRING
            value: "DEVDB_TP?TNS_ADMIN=$(TNS_ADMIN)"
        volumeMounts:
          - name: tns-admin
            mountPath: /oracle/tns_admin
          # uncomment and customize the next item if you want to provide custom metrics definitions
          #- name: config-volume
          #  mountPath: /oracle/observability/txeventq-metrics.toml
          #  subPath: txeventq-metrics.toml
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"  
        ports:
        - containerPort: 8080
      restartPolicy: Always
      volumes:
        - name: tns-admin
          configMap:
            name: db-metrics-tns-admin
        # uncomment and customize the next item if you want to provide custom metrics definitions
        #- name: config-volume
        #  configMap:
        #    name: db-metrics-txeventq-exporter-config```

--> Verify the exporter "kubectl logs -f svc/metrics-exporter -n orao-ha"
3)DEPLOY THE exporter svc 

kubectl apply -f metrics-exporter-service.yaml

```
## Copyright (c) 2021, 2023, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
apiVersion: v1
kind: Service
metadata:
  name: metrics-exporter-svc
  namespace: orao-ha
  labels:
    app: metrics-exporter
    release: stable
spec:
  type: ClusterIP
  ports:
    - port: 9161
      name: metrics
      targetPort: 9161
  selector:
    app: metrics-exporter

```
4) Create a Kubernetes service monitor
CMD : <kubectl apply -f metrics-service-monitor.yaml -n orao-ha>

```
## Copyright (c) 2021, 2023, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: prometheus-metrics-exporter
  namespace: orao-ha
  labels:
    app: metrics-exporter
    release: stable
spec:
  endpoints:
    - interval: 20s
      port: metrics
  selector:
    matchLabels:
      app: metrics-exporter
```
