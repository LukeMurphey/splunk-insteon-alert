import sys
import urllib
import time
import json

import splunk.rest
from splunk import AuthenticationFailed

from insteon_control_app.search_command import SearchCommand
from send_insteon_command import SendInsteonCommandAlert, InsteonMultipleDeviceField, InsteonCommandField
 
class SendInsteonCommand(SearchCommand):
    
    def __init__(self, device=None, command=None, cmd1=None, cmd2=None):
        
        # Save the parameters
        self.device = device
        self.command = command
        self.cmd1 = cmd1
        self.cmd2 = cmd2
        
         # Initialize the class
        SearchCommand.__init__( self, run_in_preview=False, logger_name='insteon_search_command')
    
    def get_hub_info(self, session_key):
        """
        Obtain the information from the send_insteon_command alert action default stanza that will allow us to connect to the Insteon Hub.
        
        Arguments:
        session_key -- The session key to use to connect to Splunkd
        """
        
        username = None
        password = None
        hub_address = None
        hub_port = None
        
        uri = urllib.quote('/servicesNS/nobody/insteon_control/admin/alert_actions/send_insteon_command') + '?output_mode=json'
        
        try:
            serverResponse, serverContent = splunk.rest.simpleRequest(uri, method='GET', sessionKey=session_key)
            info = json.loads(serverContent)
            
            username = info['entry'][0]['content']['param.username']
            password = info['entry'][0]['content']['param.password']
            hub_address = info['entry'][0]['content']['param.address']
            hub_port = info['entry'][0]['content']['param.port']
            
        except AuthenticationFailed as e:
            raise e
        except Exception as e: 
            self.logger.exception("Error when attempting to load send_insteon_command alert action configuration")
            
            raise e
        
        return hub_address, hub_port, username, password
        
    def handle_results(self, results, session_key, in_preview):
        
        # Obtain the authentication information
        hub_address, hub_port, username, password = self.get_hub_info(session_key)
        
        # Make sure we have the information necessary to connect to Insteon
        if hub_address is None:
            self.output_results([{
                                  'message' : 'Insufficient information to connect to Insteon hub: missing address'
                                  }])
            return False
        elif hub_port is None:
            self.output_results([{
                                  'message' : 'Insufficient information to connect to Insteon hub: missing port'
                                  }])
            return False
        elif username is None:
            self.output_results([{
                                  'message' : 'Insufficient information to connect to Insteon hub: missing username'
                                  }])
            return False
        elif password is None:
            self.output_results([{
                                  'message' : 'Insufficient information to connect to Insteon hub: missing password'
                                  }])
            return False
        
        # Validate and convert the device field
        devices = InsteonMultipleDeviceField.normalize_device_ids(self.device)
        
        # Validate and convert the command field
        cmd1 = self.cmd1
        cmd2 = self.cmd2
        times = 1
        
        command_info = None
        
        if self.command is not None:
            command_info = InsteonCommandField.get_detailed_info_from_command(self.command)
            
            # Populate from the command_info if we got one
            if command_info is not None:
                
                if cmd1 is None:
                    cmd1 = command_info.cmd1
                    
                if cmd2 is None:
                    cmd2 = command_info.cmd2
                    
                times = command_info.times
                
        # Stop if we didn't get the proper command information
        if cmd1 is None:
            self.output_results([{
                                  'message' : 'Insufficient information provided: missing cmd1'
                                  }])
            return False
        elif cmd1 is None:
            self.output_results([{
                                  'message' : 'Insufficient information provided: missing cmd2'
                                  }])
            return False
        
        # This will store the results that we will output at the end
        results = []
        
        # Execute the command for each device
        for device in devices:
            results.extend(self.call_insteon_web_api_repeatedly( hub_address, hub_port, username, password, device, cmd1, cmd2, times ))
            time.sleep(2*SendInsteonCommandAlert.SLEEP_BETWEEN_CALL_DURATION)
    
        # Output the results so that users know if the commands succeeded
        self.output_results(results)
    
    def call_insteon_web_api_repeatedly(self, address, port, username, password, device, cmd1, cmd2, times):
        """
        Perform a call to the Insteon Web API.
        
        Arguments:
        address -- The address of the Insteon Hub
        port -- The port of the Insteon Hub web-server
        username -- The username to authenticate to the Insteon Hub
        password -- The password to authenticate to the Insteon Hub
        device -- The device to send the command to
        cmd1 -- The hex string of the first command portion of the command
        cmd2 -- The hex string of the second command portion of the command
        times -- How many times to call the API
        """
        
        if times < 1:
            times = 1
            
        # This will store the results to be outputted in the search results
        results = []
        
        # Call the API the number of times requested
        for i in range(0, times):
            
            # Call the API
            result = SendInsteonCommandAlert.call_insteon_web_api(address, port, username, password, device, cmd1, cmd2, self.logger)
            
            if result:
                results.append({
                                  'message' : 'Successfully sent Insteon command to hub',
                                  'cmd1' : cmd1,
                                  'cmd2' : cmd2,
                                  'device' : device
                                   })
            else:
                results.append({
                                  'message' : 'Failed to send Insteon command to hub',
                                  'cmd1' : cmd1,
                                  'cmd2' : cmd2,
                                  'device' : device
                                   })
            
            # If this isn't the last call, then wait a bit before calling it again
            if i < times:
                time.sleep(SendInsteonCommandAlert.SLEEP_BETWEEN_CALL_DURATION)
                
            # Return the results
            return results
        
if __name__ == '__main__':
    try:
        SendInsteonCommand.execute()
        sys.exit(0)
    except Exception as e:
        print e