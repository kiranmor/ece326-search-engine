# to terminate a EC2 instance
import boto3  
import sys  

def load_credentials():
    try:
        with open('credentials.txt', 'r') as file:
            lines = file.readlines()
            access_key = lines[0].strip()
            secret_key = lines[1].strip()
            aws_region = lines[2].strip()
            return access_key, secret_key, aws_region
    except FileNotFoundError:
        print("Credentials file not found.")
        sys.exit(1)
    except IndexError:
        print("Credentials file is improperly formatted.")
        sys.exit(1)

def terminate_instance(instance_id, access_key, secret_key):
    print("Terminating started for EC2 instance")
    ec2 = boto3.client('ec2', 
                       aws_access_key_id=access_key,
                       aws_secret_access_key=secret_key, 
)
    try:
        response = ec2.terminate_instances(InstanceIds=[instance_id])
        state = response['TerminatingInstances'][0]['CurrentState']['Name']
        print(f"The current state of the instance is: {state}")
        print(f"Termination has been completed.")
    except Exception as e:
        print(f"Failed to terminate EC2 instance: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("AWS EC2 Termination Script")
    print("Loading AWS credentails from the file")

    access_key, secret_key, aws_region = load_credentials()

    instance_id = input("Enter the EC2 Instance ID to terminate: ").strip()
    if not instance_id:
        print("No Instance found.")
        sys.exit(1)

    terminate_instance(instance_id, access_key, secret_key)