def _modify_cluster():
    _slog("INFO", "Modifying backup retention for cluster " + ARGS.TGT_CLUSTER)
    try:
        session = boto3.session.Session()
        client = session.client(service_name="rds", region_name=REGION_NAME, config=config)

        while True:
            desc = _desc_cluster(ARGS.TGT_CLUSTER)
            if desc == "ERROR":
                _slog("ERROR", f"Failed to describe cluster {ARGS.TGT_CLUSTER}")
                _abort()
            cluster_status = desc['DBClusters'][0]['Status']
            _slog("INFO", f"Current cluster status: {cluster_status}")
            if cluster_status == "available":
                break
            time.sleep(30)
 
        response = client.modify_db_cluster(
            DBClusterIdentifier=ARGS.TGT_CLUSTER,
            BackupRetentionPeriod=BACKUP_RETENTION,
            ApplyImmediately=True
        )
        _slog("INFO", "Target Cluster modify started")
        print (response)
 
        while True:
            desc = _desc_cluster(ARGS.TGT_CLUSTER)
            if desc == "ERROR":
                _slog("ERROR", f"Failed to describe cluster {ARGS.TGT_CLUSTER}")
                _abort()
            cluster_status = desc['DBClusters'][0]['Status']
            _slog("INFO", f"Cluster status after modify: {cluster_status}")
            if cluster_status == "available":
                break
            time.sleep(30)
 
        _slog("INFO", "Update backup retention completed successfully")
 
    except Exception as clone_cluster:
        _slog("ERROR", f"Unable to update backup retention for target cluster : {ARGS.TGT_CLUSTER}, {clone_cluster}")
        _abort()
        
        
        
=======================================

def _modify_cluster():
    _slog("INFO", "Modifying backup retention for cluster " + ARGS.TGT_CLUSTER)
    try:
        session = boto3.session.Session()
        client = session.client(service_name="rds", region_name=REGION_NAME, config=config)
        response = client.modify_db_cluster(DBClusterIdentifier=ARGS.TGT_CLUSTER,
            BackupRetentionPeriod=BACKUP_RETENTION,
            ApplyImmediately=True)
        _slog("INFO", "Target Cluster modify started" )
        print (response)
        time.sleep(30)
        chk_status = _desc_cluster(ARGS.TGT_CLUSTER)
        cluster_status = chk_status['DBClusters'][0]['Status']
        cluster_status = response['DBCluster']['Status']
        print ("Cluster Satus " + str(cluster_status))
        while cluster_status != "available":
            chk_status = _desc_cluster(ARGS.TGT_CLUSTER)
            cluster_status = chk_status['DBClusters'][0]['Status']
            time.sleep(30)
        _slog("INFO", "update backup retention completed")
    except Exception as clone_cluster:
        _slog("ERROR", f"Unable to update backup retension for target cluster : {ARGS.TGT_CLUSTER}  , {clone_cluster}")
        _abort()
