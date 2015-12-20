import sys
import json
import logging
import httplib2
import time

from insteon_alert_app.modular_alert import ModularAlert, Field, PortField, FieldValidationException

class InsteonCommandField(Field):
    """
    Represents shortcuts to common Insteon commands.
    
    This and the default/data/ui/alerts/send_insteon_command.html must be keep in sync.
    """
    
    class InsteonCommandMeta:
        
        def __init__(self, cmd1, cmd2, response_expected=False, times=1):
            self.cmd1 = cmd1
            self.cmd2 = cmd2
            self.response_expected = response_expected
            self.times = times
    
    # These commands are a list of the shortcuts
    # The tuple consists of:
    #    1) cmd1
    #    2) cmd2
    #    3) should the command be polled for a response
    #    4) how many times the command should be called
    COMMANDS = {
                'on' :                    ('11', 'FF', False, 1),
                'fast_on' :               ('12', 'FF', False, 1),
                'off' :                   ('13', 'FF', False, 1),
                'fast_off' :              ('14', 'FF', False, 1),
                'status' :                ('15', 'FF', True , 1),
                'beep' :                  ('30', '01', False, 1),
                'beep_two_times' :        ('30', '01', False, 2),
                'beep_three_times' :      ('30', '01', False, 3),
                'beep_four_times' :       ('30', '01', False, 4),
                'beep_five_times' :       ('30', '01', False, 5),
                'beep_ten_times' :        ('30', '01', False, 10),
                'imeter_status' :         ('82', '00', True , 1),
                'imeter_reset' :          ('80', '00', False, 1),
                'ping' :                  ('0F', '00', True , 1),
                }
    
    def to_python(self, value):
        
        v = Field.to_python(self, value)
        
        command_data = InsteonCommandField.COMMANDS.get(v.lower().strip())
        
        if command_data is None:
            raise FieldValidationException("This is not a recognized Insteon command")
        else:
            
            return InsteonCommandField.InsteonCommandMeta(command_data[0], command_data[1], command_data[2], command_data[3])
            """
            return {
                    'cmd1' : command_data[0],
                    'cmd2' : command_data[1],
                    'response_expected' : command_data[2],
                    'times' : command_data[3]
                    }
            """

class SendInsteonCommandAlert(ModularAlert):
    """
    This alert action supports sending commands to an Insteon Hub via its web interface.
    """
    
    # This indicates how long to wait between each call when a command is supposed to be called several times
    SLEEP_BETWEEN_CALL_DURATION = 0.5
    
    def __init__(self, **kwargs):
        params = [
                    # Fields to identify the hub to connect to
                    Field("address", empty_allowed=False, none_allowed=False),
                    PortField("port", empty_allowed=False, none_allowed=False),
                    
                    # Authentication data for authenticating to the hub
                    Field("password", empty_allowed=False, none_allowed=False),
                    Field("username", empty_allowed=False, none_allowed=False),
                    
                    # The command to send
                    InsteonCommandField("command", empty_allowed=False, none_allowed=False),
                    Field("device", empty_allowed=False, none_allowed=False)
        ]
        
        ModularAlert.__init__( self, params, logger_name="send_insteon_command_alert", log_level=logging.DEBUG )
        
    def call_insteon_web_api(self, address, port, username, password, device, cmd1, cmd2, out_stream):
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
        out_stream -- The output stream to send response messages to
        """
        
        # Build the URL to perform the action
        url = "http://%s:%s/3?0262%s0F%s%s=I=3" % (address, port, device, cmd1, cmd2)
        
        self.logger.debug("Calling Insteon Hub API with url=%s", url)
        
        # Perform the action
        # Make the HTTP object
        http = httplib2.Http(timeout=5, disable_ssl_certificate_validation=True)
        
        # Add in the credentials
        http.add_credentials(username, password)
        
        # Perform the operation
        response, content = http.request(url, 'GET')
        
        if response.status == 200:
            print >> out_stream, "Operation performed successfully, " + self.create_event_string({
                                                                                                   'url' : url
                                                                                                 })
        else:
            print >> out_stream, "Operation failed, " + self.create_event_string({
                                                                                 'status_code' : response.status
                                                                                 })
            
    def call_insteon_web_api_repeatedly(self, address, port, username, password, device, cmd1, cmd2, out_stream, times):
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
        out_stream -- The output stream to send response messages to
        times -- How many times to call the API
        """
        
        if times < 1:
            times = 1
        
        # Call the API the number of times requested
        for i in range(0, times):
            
            # Call the API
            self.call_insteon_web_api(address, port, username, password, device, cmd1, cmd2, out_stream)
            
            # If this isn't the last call, then wait a bit before calling it again
            if i < times:
                time.sleep(SendInsteonCommandAlert.SLEEP_BETWEEN_CALL_DURATION)
    
    def run(self, cleaned_params, payload, out_stream):
        
        # Get the information we need to execute the alert action
        address = cleaned_params.get('address', None)
        port = cleaned_params.get('port', 25105)
        
        password = cleaned_params.get('password', None)
        username = cleaned_params.get('username', None)
        
        device = cleaned_params.get('device', None)
        command = cleaned_params.get('command', None)
        
        # Call the API the number of times requested
        self.call_insteon_web_api_repeatedly(address, port, username, password, device, command.cmd1, command.cmd2, out_stream, command.times)
        
"""
If the script is being called directly from the command-line, then this is likely being executed by Splunk.
"""
if __name__ == '__main__':
    
    # Make sure this is a call to execute
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        
        try:
            insteon_alert = SendInsteonCommandAlert()
            insteon_alert.execute()
            sys.exit(0)
        except Exception as e:
            print >> sys.stderr, "Unhandled exception was caught, this may be due to a defect in the script:" + str(e) # This logs general exceptions that would have been unhandled otherwise (such as coding errors)
            raise
        
    else:
        print >> sys.stderr, "Unsupported execution mode (expected --execute flag)"
        sys.exit(1)