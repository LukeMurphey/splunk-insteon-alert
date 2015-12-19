import sys
import json

def normalize_device_id(device):
    return device

# Issue alert action
def execute_insteon_command(result, config):
    
    # Get the information we need to execute the alert action
    address = config.get('address')
    port = config.get('port')
    device = config.get('device')
    command = config.get('command')
    
    # Normalize the device ID (so that a device of "0a:34:67" would be converted to "0A3467")
    device = normalize_device_id(device)
    
    print >> sys.stderr, "INFO Config: " + str(config)
    
    # Make the URL
    url = "http://%s:%s/3?0262%s0F%sFF=I=3" % (address, port, device, command)
    
    print >> sys.stderr, "INFO Test Insteon: " + url

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        try:
            # Get the info from Splunk
            input = sys.stdin.read()
            payload = json.loads(input)
            
            f = open('/Users/lmurphey/Desktop/modalert.txt', 'w')
            f.write(input)
            f.close()
            
            config = payload.get('configuration')
            result = payload.get('result')

            # Execute the command
            execute_insteon_command(result, config)
            
        except Exception, e:
            print >> sys.stderr, "ERROR Unexpected error: %s" % e
            sys.exit(3)
    else:
        print >> sys.stderr, "FATAL Unsupported execution mode (expected --execute flag)"
        sys.exit(1)
