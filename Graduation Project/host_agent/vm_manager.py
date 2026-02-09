import subprocess
import time


class VM:
    """A class to manage virtual machines using VMware vmrun."""
    
    def __init__(self, vmx_path, guest_user, guest_pass, vmrun_path=None):
        """
        Initialize a VM instance.
        
        Args:
            vmx_path (str): Path to the VM configuration file (.vmx)
            guest_user (str): Username for guest OS access
            guest_pass (str): Password for guest OS access
            vmrun_path (str): Path to vmrun executable
        """
        self.vmx_path = vmx_path
        self.guest_user = guest_user
        self.guest_pass = guest_pass
        self.vmrun_path = vmrun_path or r"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"
    
    def wait_for_guest_ready(self, timeout=300):
        """Waits for VMware Tools to be running in the guest."""
        print("Waiting for VMware Tools to start...")
        start_time = time.time()
        
        check_cmd = [self.vmrun_path, "-T", "ws", "checkToolsState", self.vmx_path]
        
        while time.time() - start_time < timeout:
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            # 'running' is the expected output when ready
            if "running" in result.stdout:
                print("VMware Tools is active. Guest is ready.")
                return True
            time.sleep(5)
        
        print("Timeout: VMware Tools never started.")
        return False
    
    def check_file_existence(self, guest_file_path):
        """Check if a file exists in the guest VM."""
        # Command to check if file exists in guest
        check_cmd = [
            self.vmrun_path, "-T", "ws", 
            "-gu", self.guest_user, "-gp", self.guest_pass, 
            "fileExistsInGuest", self.vmx_path, guest_file_path
        ]

        # subprocess.run will return an 'exit code'
        # 0 usually means the file exists; non-zero means it does not
        result = subprocess.run(check_cmd, capture_output=True)

        if result.returncode == 0:
            print("The file exists inside the Guest VM.")
            return 0
        else:
            print("The file does NOT exist inside the Guest VM.")
            return 1
    
    def send_file(self, host_file, guest_destination):
        """Copy a file from host to guest VM."""
        # 1. Copy file from Host to Guest
        copy_cmd = [
            self.vmrun_path, "-T", "ws", 
            "-gu", self.guest_user, "-gp", self.guest_pass, 
            "CopyFileFromHostToGuest", self.vmx_path, host_file, guest_destination
        ]

        # Run the commands
        subprocess.run(copy_cmd)
        print("File copied successfully.")
    
    def execute_file(self, guest_destination):
        """Execute a file on the guest VM."""
        # Note the placement of -activeWindow after runProgramInGuest
        exec_cmd = [
            self.vmrun_path, 
            "-T", "ws", 
            "-gu", self.guest_user, 
            "-gp", self.guest_pass, 
            "runProgramInGuest", 
            self.vmx_path, 
            "-activeWindow",  # Moved here
            guest_destination
        ]
        
        try:
            subprocess.run(exec_cmd, check=True)
            print("Execution started successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to execute: {e}")
    
    def start(self):
        """Start the VM (runs it in the background)."""
        subprocess.run([self.vmrun_path, "-T", "ws", "start", self.vmx_path, "nogui"])
        print("VM start command sent.")
    
    def stop(self):
        """Stop the VM gracefully."""
        subprocess.run([self.vmrun_path, "-T", "ws", "stop", self.vmx_path, "soft"])
        print("VM stop command sent.")
    
    def get_ip(self):
        """Get the IP address of the VM."""
        # Command to get the IP
        cmd = [self.vmrun_path, "-T", "ws", "getGuestIPAddress", self.vmx_path]
        
        try:
            # We use capture_output=True to grab the IP string from the terminal
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            ip = result.stdout.strip()
            return ip
        except subprocess.CalledProcessError:
            return "IP not found (Is the VM running and VMware Tools installed?)"
    
    def revert_to_snapshot(self, snapshot_name=None):
        """Revert the VM to a snapshot."""
        # If no name is provided, it reverts to the 'current' (most recent) snapshot
        if snapshot_name:
            cmd = [self.vmrun_path, "-T", "ws", "revertToSnapshot", self.vmx_path, snapshot_name]
            print(f"Reverting to snapshot: {snapshot_name}...")
        else:
            # Note: some versions of vmrun require a name. 
            # If this fails, you must provide the specific name.
            print("Error: Please provide a snapshot name.")
            return

        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Success: VM reverted.")
        else:
            print(f"Failed to revert. Error: {result.stderr}")
    
    def list_snapshots(self):
        """List all available snapshots for the VM."""
        cmd = [self.vmrun_path, "-T", "ws", "listSnapshots", self.vmx_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("Available Snapshots:")
        print(result.stdout)
    
    def create_snapshot(self, snapshot_name):
        """Create a snapshot of the VM."""
        # Syntax: vmrun snapshot [path] [name]
        cmd = [self.vmrun_path, "-T", "ws", "snapshot", self.vmx_path, snapshot_name]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Snapshot '{snapshot_name}' created successfully.")
        else:
            print(f"Error creating snapshot: {result.stderr}")
    
    def delete_snapshot(self, snapshot_name):
        """Delete a snapshot from the VM."""
        # 'andDeleteChildren' is optional: it deletes this snapshot AND any linked to it
        cmd = [self.vmrun_path, "-T", "ws", "deleteSnapshot", self.vmx_path, snapshot_name]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Snapshot '{snapshot_name}' deleted and merged.")
        else:
            print(f"Error deleting snapshot: {result.stderr}")
    
    def set_to_host_only(self):
        """Set the VM's network adapter to host-only mode."""
        with open(self.vmx_path, 'r') as f:
            lines = f.readlines()

        new_lines = []
        found_type = False
        
        for line in lines:
            # Update the connection type if it exists
            if line.startswith('ethernet0.connectionType'):
                new_lines.append('ethernet0.connectionType = "hostonly"\n')
                found_type = True
            # Remove specific vnet settings to let it default to Host-only (VMnet1)
            elif line.startswith('ethernet0.vnet'):
                continue 
            else:
                new_lines.append(line)

        # If the line wasn't there at all, add it
        if not found_type:
            new_lines.append('ethernet0.connectionType = "hostonly"\n')

        with open(self.vmx_path, 'w') as f:
            f.writelines(new_lines)
            
        print("Network adapter 0 set to Host-only.")
    
    def allow_fastapi_firewall(self, port=5003):
        """Allow FastAPI port through Windows firewall in the guest VM."""
        # The Windows command to add a firewall rule
        # Name: "FastAPI_Inbound"
        # Action: Allow
        # Direction: In (Inbound)
        # Protocol: TCP
        rule_name = "FastAPI_Server"
        firewall_cmd = (
            f'netsh advfirewall firewall add rule name="{rule_name}" '
            f'dir=in action=allow protocol=TCP localport={port}'
        )

        exec_cmd = [
            self.vmrun_path, "-T", "ws", 
            "-gu", self.guest_user, "-gp", self.guest_pass, 
            "runProgramInGuest", self.vmx_path, 
            "C:\\Windows\\System32\\cmd.exe", "/c", firewall_cmd
        ]
        
        result = subprocess.run(exec_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Firewall rule added: Port {port} is now open.")
        else:
            print(f"Failed to set firewall: {result.stderr}")
    
    @staticmethod
    def clone(source_vmx, destination_vmx, new_name, vmrun_path=None):
        """Create a linked clone of a VM (static method)."""
        if vmrun_path is None:
            vmrun_path = r"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"
        
        # 1. Define the command list
        clone_cmd = [
            vmrun_path, 
            "-T", "ws",                     # Target: Workstation
            "clone",                        # Action: Clone
            source_vmx,                     # Path to Golden Image
            destination_vmx,                # Where to save the new VM
            "linked",                       # Mode: Linked (Fast) or Full (Slow)
            f"-cloneName={new_name}"         # How it appears in the VMware list
        ]

        # 2. Execute the command
        print(f"Creating linked clone: {new_name}...")
        result = subprocess.run(clone_cmd, capture_output=True, text=True)

        # 3. Check if it worked
        if result.returncode == 0:
            print("Clone created successfully!")
            return True
        else:
            print(f"Cloning failed: {result.stderr}")
            return False


    

def main():
    # Path to your VM's .vmx file
    vmx_path = r"D:\Virtual Machines\Windows 8.x x64\Windows 8.x x64.vmx"
    guest_user = "abdo_"
    guest_pass = "malware"

    vm = VM(vmx_path, guest_user, guest_pass)

    # Start the VM
    # vm.start()
    # # Wait for the guest to be ready  
    # if vm.wait_for_guest_ready():
    #     # Check if the file exists in the guest
    #     guest_file_path = r"C:\vm_agent.exe"

    #     # If the file doesn't exist, send it and execute
    #     if vm.check_file_existence(guest_file_path) != 0:
    #         host_file = r"D:\Graduation Project\vm_agent\dist\vm_agent.exe"
    #         vm.send_file(host_file, guest_file_path)
    #         vm.execute_file(guest_file_path)

    #     vm.allow_fastapi_firewall(port=5003)
    #     print(vm.get_ip())

    # vm.set_to_host_only()
    vm.allow_fastapi_firewall(port=5003)
    print(vm.get_ip())


    # vm.send_file(r"D:\Graduation Project\vm_agent\dist\vm_agent.exe", r"C:\vm_agent.exe")
    # vm.execute_file(r"C:\vm_agent.exe")


    # vm.stop()

if __name__ == "__main__":
    main()