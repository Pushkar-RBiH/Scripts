import docker
import time
import subprocess

def start_docker_desktop():
    try:
        # Command to start Docker Desktop on Windows
        subprocess.run(["start", "docker"], shell=True)
        
        # Wait for Docker Desktop to start up
        print("Starting Docker Desktop...")
        time.sleep(30)  # Adjust the sleep duration as needed
        print("Docker Desktop started.")
    except Exception as e:
        print(f"An error occurred while starting Docker Desktop: {e}")

def is_docker_running():
    try:
        client = docker.from_env()
        client.ping()
        return True
    except docker.errors.APIError:
        return False

def start_cassandra():
    if not is_docker_running():
        print("Docker Desktop is not running. Attempting to start Docker Desktop...")
        start_docker_desktop()
        if not is_docker_running():
            print("Failed to start Docker Desktop. Please start Docker Desktop manually and try again.")
            return

    client = docker.from_env()

    # Remove the existing network if it exists
    try:
        network = client.networks.get('cassandra')
        network.remove()
        print("Removed existing 'cassandra' network.")
    except docker.errors.NotFound:
        print("'cassandra' network does not exist. No need to remove.")

    # Create a new network
    client.networks.create('cassandra')
    print("Created 'cassandra' network.")

    # Run the Cassandra container
    container = client.containers.run(
        'cassandra',
        detach=True,
        ports={'9042/tcp': 9042},
        name='cassandra',
        hostname='cassandra',
        network='cassandra',
        remove=True
    )
    print("Started Cassandra container.")
    print("Container ID:", container.id)

    # Wait for Cassandra to be ready
    while True:
        try:
            result = subprocess.run(
                ["docker", "exec", container.id, "cqlsh", "-e", "DESCRIBE CLUSTER"],
                capture_output=True,
                text=True
            )
            if "Connection error" not in result.stderr:
                print("Cassandra is ready.")
                break
        except Exception as e:
            print("Waiting for Cassandra to be ready...")
        time.sleep(5)

    # Create the keyspace
    subprocess.run(
        ["docker", "exec", container.id, "cqlsh", "-e",
         "CREATE KEYSPACE IF NOT EXISTS cks_dev WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 };"]
    )
    print("Keyspace 'cks_dev' created.")

    # Use the keyspace and create the tables
    table_commands = [
        """
        CREATE TABLE IF NOT EXISTS cks_dev.lender_callback_info (
            servicename text,
            clientid text,
            lendercallbackurl text,
            created_by text,
            created_on timestamp,
            type text,
            customheaders map<text, text>,
            PRIMARY KEY (servicename, clientid)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS cks_dev.tealrequests (
            uuid uuid PRIMARY KEY,
            client_id text,
            initiation_timestamp text,
            query_id text,
            report_id text,
            txncode text,
            cersai_search_report map<text, text>,
            digital_property_search_report map<text, text>,
            jwttoken text,
            version text,
            cersaistatus text,
            dpsrstatus text
        );
        """
    ]

    for command in table_commands:
        subprocess.run(["docker", "exec", container.id, "cqlsh", "-e", command])
    print("Tables 'lender_callback_info' and 'tealrequests' created.")

    # Insert data into lender_callback_info table
    insert_command = """
    INSERT INTO cks_dev.lender_callback_info (lendercallbackurl, customheaders, clientid, servicename, type, created_by, created_on)
    VALUES (
        'https://pizzapuff.requestcatcher.com/',
        {'Header1': 'Value1', 'Header2': 'Value2'},
        'MDRtbTVpREhrZHpGbHZGalpXOGZ6Q2QwU1g0YQ==',
        'propsearchteal',
        'TypeValue',
        'Parth Pushkar',
        toTimestamp(now())
    );
    """

    subprocess.run(["docker", "exec", container.id, "cqlsh", "-e", insert_command])

    print("Inserted data into 'lender_callback_info' table.")

if __name__ == "__main__":
    start_cassandra()
