import psycopg2
import boto3
import json
from datetime import timedelta
 
def get_aws_session_from_secret(secret_name='snap-keys', region_name='us-east-1'):
    secrets_manager = boto3.client('secretsmanager', region_name='us-east-1')
    
    try:
        response = secrets_manager.get_secret_value(SecretId='snap-keys')
        credentials = json.loads(response['SecretString']) 
        aws_access_key_id = credentials['aws_access_key_id']
        aws_secret_access_key = credentials['aws_secret_access_key']
 
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        sts_client = session.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        account_name_map = {
            "734006704080": "v3locity",
            "866159464259": "v3locitydev",
            
        }
        account_name = account_name_map.get(account_id, account_id)
        print(f" Connected to AWS account: {account_name}")

        return session

    except Exception as e:
        print(f"Error retrieving AWS credentials from Secrets Manager: {e}")
        return None
 
def get_snapshot_start_time(session, cluster_identifier, snapshot_name, region='us-east-1'):
    client = session.client('rds', region_name=region)

    try:
        response = client.describe_db_cluster_snapshots(
            DBClusterIdentifier=cluster_identifier,
            SnapshotType='manual',
            Filters=[
                {'Name': 'db-cluster-snapshot-id', 'Values': [snapshot_name]}
            ]
        )

        snapshots = response.get('DBClusterSnapshots', [])

        if not snapshots:
            raise Exception(f"Snapshot '{snapshot_name}' not found for cluster '{cluster_identifier}'.")
        return snapshots[0]['SnapshotCreateTime']

    except Exception as e:
        raise Exception(f"Error fetching snapshot: {e}")
 
def catalog_snapshot(
    cluster_name, client_name, snapshot_name,
    email_notification, retention_days, region='us-east-1'
):
 
    # === Get snapshot creation time ===

    try:
        backup_time = get_snapshot_start_time(session, cluster_name, snapshot_name, region)

    except Exception as e:
        print(str(e))
        return
 
    dnd_upto = backup_time + timedelta(days=retention_days)
 
    # === DB connection parameters (hardcoded for now) ===

    host = "vitechpgqa-cluster.cluster-ctcsve9jprsn.us-east-1.rds.amazonaws.com"
    dbname = "vitechpgqa"
    user = "dbadmin"
    password = "vitechdba2016"
 
    insert_sql = """

        INSERT INTO dbadmin.pg_db_adhoc_backup_request_hst (
            db_connect_string, backup_start_time, email_notification,
            enable_archiving, status, skip_pre_backup_check,
            backup_requested_by, backup_requested_date,
            updated_by, updated_date, deleted_by, deleted_date,
            dml_operation, client_name, backup_retention_days,
            long_term_backup, backup_retention_copies, target_db_ip,
            backup_type, snapshot_name, backup_location, dnd, dnd_upto
        )

        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s)

    """

    insert_values = (
        cluster_name,
        backup_time,
        email_notification,
        '',
        'SUCCESS',
        'N',
        'AWS Console',
        backup_time,
        '',
        None,
        None,
        'U',
        client_name,
        retention_days,
        '',
        2,
        '',
        'SNAPSHOT',
        snapshot_name,
        '',
        'Y',
        dnd_upto
    )
 
    try:
        conn = psycopg2.connect(
            host=host, dbname=dbname,
            user=user, password=password
        )

        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(insert_sql, insert_values)
        print(f"\n Cataloged snapshot '{snapshot_name}' for client '{client_name}' ({retention_days} days).")
        print(f"   Backup Time (UTC): {backup_time}")
        print(f"   DND Until        : {dnd_upto}\n")

    except Exception as e:
        print(f"\n Database insert failed: {e}\n")

    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()
 
# === Prompt for required inputs ===
 
if __name__ == "__main__":
    session = get_aws_session_from_secret()
    if session is None:
        exit(1)
    cluster_name = input("Enter RDS Cluster Identifier (e.g. test-cluster): ").strip()
    client_name = input("Enter Client Name (e.g. TEST): ").strip()
    snapshot_name = input("Enter Snapshot Name (exactly from AWS): ").strip()
    email_notification = input("Enter Email Notification Address: ").strip()

    try:
        retention_days = int(input("Enter Retention Days (e.g. 14): ").strip())

    except ValueError:
        print("Invalid number for retention days.")
        exit(1)

    region = input("Enter AWS Region [us-east-1]: ").strip() or "us-east-1"
 
    catalog_snapshot(
        cluster_name, client_name, snapshot_name,
        email_notification, retention_days, region
    )
