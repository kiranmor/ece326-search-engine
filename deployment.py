# to deploy on EC2
import boto3  
import sys  
import time
import os
import subprocess
import paramiko
BASE_DIR = os.path.dirname(os.path.abspath(__file__))



# loading the credentials
def load_credentials():
    try:
        with open(r"credentials.txt", 'r') as file:
            lines = file.readlines()
            access_key = lines[0].strip()
            print("Loading the access key")
            secret_key = lines[1].strip()
            print("Loading the secret key")
            aws_region = lines[2].strip()
            print("The AWS region is:", aws_region)
            return access_key, secret_key, aws_region
    except FileNotFoundError:
        print("Couldn't found the credentials.txt file.")
        sys.exit(1)
    except IndexError:
        print("Credential file is not formatted properly.")
        sys.exit(1)


def deploy_instance(access_key, secret_key, region):
    print("Deployment has been started for EC2 instance...sit back and relax")
    ec2 = boto3.resource('ec2', 
                         aws_access_key_id=access_key,
                         aws_secret_access_key=secret_key, 
                         region_name=region
    )
    try:
        instances = ec2.create_instances(
            ImageId='YOUR_AMI_ID',  # Ubuntu 22.04
            MinCount=1,
            MaxCount=1,
            InstanceType='t3.micro',
            KeyName='YOUR_KEY_PAIR_NAME',
            SecurityGroupIds=['YOUR_SECURITY_GROUP_ID'] # security group
        )

        instance = instances[0]
        print(f"Instance {instance.id} is being created.")
        print("Waiting for the instance to be in running state.")
        instance.wait_until_running()
        instance.reload()
        print("\n")

#we can change a bit here
        print(f"The deplyed instance id is: {instance.id}")
        print(f"The public ip of instance is: {instance.public_ip_address}")
        print(f"The public dns of instance is: {instance.public_dns_name}")
        return instance.id
    except Exception as e:
        print(f"The deployment of EC2 has been failed: {e}")
        sys.exit(1)

def ssh_into_instance(instance_dns):
    print("Trying to SSH into instance")
        
    key_path = os.path.join(BASE_DIR, "YOUR_KEY_FILE.pem")
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    for attempt in range(12):
        try:
            ssh_client.connect(
                instance_dns,
                username='ubuntu',
                key_filename=key_path,
                timeout=10
            )
            print("SSH connection has been established.")
            return ssh_client
        except Exception as e:
            print(f"SSH connection failed (attempt {attempt+1}/12): {e}")
            time.sleep(10)

    raise Exception("SSH connection failed after multiple attempts.")



def run_commands_on_ec2(ssh_client):
    print("\n Installing System Dependencies ---")
    commands = [
        "sudo apt update -y",
        "sudo systemctl start apache2",
        "sudo apt install apache2 -y",
        "sudo apt install python3-pip -y",
        "sudo systemctl enable apache2"
    ]
    for command in commands:
        print(f"Running command: {command}")
        stdin, stdout, stderr = ssh_client.exec_command(command)
        error_output = stderr.read().decode()
        if error_output:
            print("Error executing command:", error_output)
    print("All commands executed.")


def create_remote_directory(sftp, remote_path):
    dirs = []
    remote_path = remote_path.replace('\\', '/')
    
    while remote_path and remote_path != '/':
        try:
            sftp.stat(remote_path)
            break
        except FileNotFoundError:
            dirs.append(remote_path)
            remote_path = os.path.dirname(remote_path)
    
    for directory in reversed(dirs):
        try:
            sftp.mkdir(directory)
            print(f"Created remote directory: {directory}")
        except IOError:
            pass


def copy_folder_to_ec2_recursive(sftp, local_folder, remote_folder):
    create_remote_directory(sftp, remote_folder)
    
    for item in os.listdir(local_folder):
        if item.startswith('.') or item == '__pycache__':
            continue 
            
        local_path = os.path.join(local_folder, item)
        remote_path = f"{remote_folder}/{item}".replace('\\', '/')

        if os.path.isfile(local_path):
            sftp.put(local_path, remote_path)
        elif os.path.isdir(local_path):
            copy_folder_to_ec2_recursive(sftp, local_path, remote_path)



def run_app_remote(ssh_client, remote_root):
    print("\n Running app...")
    
    commands = [
        f"pip3 install -r {remote_root}/requirements.txt",
        "pkill -f app.py || true",  # Kill old instance if running
        # Running in background with nohup
        f"cd {remote_root}/frontend && nohup python3 app.py > output.log 2>&1 &"
    ]
    
    for cmd in commands:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
        
        # We wait for pip, but NOT for nohup (because nohup runs forever)
        if "nohup" not in cmd:
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                print(f"  Error: {stderr.read().decode()}")
        else:
            print("App has been started in background.")

def deploy_meowgle(ssh_client, local_root, remote_root):
    remote_root = "/home/ubuntu/meowgle"
    print(f"Starting deployment to {remote_root}")
    print(f"Starting deployment from {local_root}")
    sftp = ssh_client.open_sftp()
    
    items_to_copy = ['frontend', 'backend', 'requirements.txt', 'README.md']

    for item in items_to_copy:
        local_item_path = os.path.join(local_root, item)
        remote_item_path = f"{remote_root}/{item}"

        if os.path.isdir(local_item_path):
            print(f"\n Copying folder: {item}")
            copy_folder_to_ec2_recursive(sftp, local_item_path, remote_item_path)
        elif os.path.isfile(local_item_path):
            print(f"\n Copying file: {item}")
            sftp.put(local_item_path, remote_item_path)
        else:
            print(f" Warning: {item} not found locally, skipping.")

    sftp.close()
    print("\nFile transfer has been complete.")
    
    # 3. RUNNING THE APP
    run_app_remote(ssh_client, remote_root)



def main(): 
    print("AWS EC2 Deployment Script")
    access_key, secret_key, aws_region = load_credentials()

    instance_id = deploy_instance(access_key, secret_key, aws_region)
    ec2 = boto3.resource('ec2', 
                         aws_access_key_id=access_key,
                         aws_secret_access_key=secret_key, 
                         region_name=aws_region
    )
    instance = ec2.Instance(instance_id)
    instance_dns = instance.public_dns_name 
   
    ssh_command = ssh_into_instance(instance_dns) 
    run_commands_on_ec2(ssh_command)  
    deploy_meowgle(ssh_command, local_root='.', remote_root='/home/ubuntu/meowgle')
    
    print("Deployment of Meowgle search engine has been completed successfully.")
    print("You can access it at: http://" + instance_dns + ":8080/")
if __name__ == "__main__":
    main()
