# coding=utf-8
import unittest
import sys
import os
import json
import re
import time
from StringIO import StringIO

sys.path.append( os.path.join("..", "src", "bin") )

from send_insteon_command import InsteonCommandField,  SendInsteonCommandAlert, InsteonDeviceField, InsteonMultipleDeviceField, InsteonExtendedDataField
from insteon_control_app.modular_alert import ModularAlert, Field, BooleanField, IPAddressField, FieldValidationException

class FakeInputStream:
    """
    The fake input stream is for testing code that accepts data from an input stream.
    """
    
    def __init__(self):
        self.value = ""
    
    def setValue(self, value):
        self.value = value
        
    def read(self):
        return self.value
        

class ModularAlertTest(unittest.TestCase):
    """
    Test the modular alert base class.
    """
    
    def test_field_empty_not_allowed(self):
        
        field = Field('test', none_allowed=True, empty_allowed=False)
        
        with self.assertRaises(FieldValidationException) as context:
            field.to_python("")
    
    def test_field_none_not_allowed(self):
        
        field = Field('test', none_allowed=False, empty_allowed=True)
        
        with self.assertRaises(FieldValidationException) as context:
            field.to_python(None)
    
    def get_modular_alert_instance(self):
        
        class TestModularAlert(ModularAlert):
            def __init__(self, **kwargs):
                params = [
                    Field("foo", empty_allowed=False),
                    BooleanField("bar", empty_allowed=False)
                ]
                
                ModularAlert.__init__( self, params, "test_modular_alert" )
                
                
            def run(self, cleaned_params, payload):
                
                return "Alert ran successfully " + self.create_event_string(cleaned_params)
                
                
        return TestModularAlert()
    
    def test_modular_alert_validation(self):
        
        test_instance = self.get_modular_alert_instance()
        
        # Ok input
        self.assertTrue(test_instance.validate({'foo' : 'foo', 'bar' : 'true'})['bar'])
        
        # Bad input
        with self.assertRaises(FieldValidationException) as context:
            test_instance.validate({'foo' : 'foo', 'bar' : '65'})
            
    def test_modular_alert_run(self):
        
        in_stream = FakeInputStream()
          
        test_instance = self.get_modular_alert_instance()
        
        input = {
                 "result": {
                            "_kv":"1",
                            "_raw": "something"
                            },
                  "configuration":{
                                   'foo' : 'FOO',
                                   'bar' : 'true'
                                   }
        }
        
        in_stream.setValue(json.dumps(input))
        
        result = test_instance.execute(in_stream)
        
        self.assertEquals( len(re.findall("Alert ran successfully", result)), 1)
        
        
class IPAddressFieldTest(unittest.TestCase):
    
    def test_validate_good_input(self):
        field = IPAddressField('device')
        
        # Good input
        self.assertEqual(field.to_python('192.168.4.1'), '192.168.4.1')
        self.assertEqual(field.to_python('192.168.004.001'), '192.168.004.001')
        
    def test_validate_bad_input(self):
        field = IPAddressField('device')
        
        # Not long enough
        with self.assertRaises(FieldValidationException) as context:
            field.to_python('192.')
            
        # Too long
        with self.assertRaises(FieldValidationException) as context:
            field.to_python('abc')
            
        # Non-hex characters
        with self.assertRaises(FieldValidationException) as context:
            field.to_python('10-0.0.1')
    
class InsteonExtendedDataFieldTest(unittest.TestCase):
    
    def test_validate_good_input(self):
        field = InsteonExtendedDataField('device')
        
        # Good input
        self.assertEqual(field.to_python('9296'), '0000000000000000000000009296')
        self.assertEqual(field.to_python('0000000000000000000000009296'), '0000000000000000000000009296')
        self.assertEqual(field.to_python('af'), '00000000000000000000000000AF')
        
    def test_validate_bad_input(self):
        field = InsteonExtendedDataField('device')
        
        # Too long
        with self.assertRaises(FieldValidationException) as context:
            field.to_python('00000000000000000000000092961')
            
        # Non-hex characters
        with self.assertRaises(FieldValidationException) as context:
            field.to_python('0g')
        
class SendInsteonCommandAlertTest(unittest.TestCase):
    """
    Test the send_insteon_command modular alert.
    """
    
    def toInt(self, str_int):
        if str_int is None:
            return None
        else:
            return int(str_int)
    
    def loadConfig(self, properties_file=None):
        
        if properties_file is None:
            properties_file = os.path.join( "..", "local.properties")
        
        fp = open(properties_file)
        regex = re.compile("(?P<key>[^=]+)[=](?P<value>.*)")
        
        settings = {}
        
        for l in fp.readlines():
            r = regex.search(l)
            
            if r is not None:
                d = r.groupdict()
                settings[ d["key"] ] = d["value"]
        
        self.username = settings.get("value.test.insteon_hub.username", None)
        self.password = settings.get("value.test.insteon_hub.password", None)
        self.address = settings.get("value.test.insteon_hub.address", None)
        self.port = self.toInt(settings.get("value.test.insteon_hub.port", 25105))
        self.device = settings.get("value.test.insteon_hub.device", None)

    def setUp(self):
        self.loadConfig()
        
    def is_configured(self):
        
        if self.username is not None and self.password is not None and self.address is not None and self.port is not None and self.device is not None:
            return True
        else:
            return False
    """
    def test_send_command(self):
        
        # Only perform this test if requested
        if self.is_configured():
            
            time.sleep(2)
            insteon_alert = SendInsteonCommandAlert()
            
            results = insteon_alert.call_insteon_web_api_repeatedly(self.address, self.port, self.username, self.password, self.device, "30", "01", 3)
            
            self.assertEquals( results[0]['success'], True)
            
    def test_execute(self):

        # Only perform this test if requested
        if self.is_configured():
            
            time.sleep(2)

            insteon_alert = SendInsteonCommandAlert()
            
            in_stream = FakeInputStream()
            
            input = {
                     "result": {
                                "_kv":"1",
                                "_raw": "something"
                                },
                      "configuration":{
                                       'address' : self.address,
                                       'port' : self.port,
                                       
                                       'username' : self.username,
                                       'password' : self.password,
                                       
                                       'device' : self.device,
                                       'command' : 'beep'
                                       }
            }
            
            in_stream.setValue(json.dumps(input))
            
            self.assertEquals(insteon_alert.execute(in_stream), 1)
    
    
    def test_parse_raw_response_sd_command(self):
        
        response = SendInsteonCommandAlert.parse_raw_response("02622C86260F15FF0602502C86262CB84E2F1900")
        
        self.assertEqual(response['last_command'], "02622C86260F15FF")
        self.assertEqual(response['last_command_cmd1'], "15")
        self.assertEqual(response['last_command_cmd2'], "FF")
        
        self.assertEqual(response['full_response'], "0602502C86262CB84E2F1900")
        self.assertEqual(response['target_device'], "2C8626")
        self.assertEqual(response['source_device'], "2CB84E")
        self.assertEqual(response['cmd1'], "19")
        self.assertEqual(response['cmd2'], "00")
    
    """
    
    def test_get_response(self):
        
        response = SendInsteonCommandAlert.call_insteon_web_api(self.address, self.port, self.username, self.password, self.device, '19', '02', True)
        print response
        self.assertEquals(response['full_response'][6:12], InsteonDeviceField.normalize_device_id(self.device, False))  
        
        
class InsteonCommandFieldTest(unittest.TestCase):
    """
    Test the InsteonCommandField that is used to convert a shortcut of a command into a real Insteon command.
    """
    
    def test_validate_good_input(self):
        ic_field = InsteonCommandField('command')
        
        # Good input
        self.assertEqual(ic_field.to_python('on').cmd1, '11')
        self.assertEqual(ic_field.to_python('on').cmd2, 'FF')
        
    def test_validate_ok_input_wrong_case(self):
        ic_field = InsteonCommandField('command')
        
        # Incorrect case, but acceptable input
        self.assertEqual(ic_field.to_python('ON').cmd1, '11')
        self.assertEqual(ic_field.to_python('OFF').cmd1, '13')
        
    def test_validate_ok_input_extra_space(self):
        ic_field = InsteonCommandField('command')
        
        # Leading space
        self.assertEqual(ic_field.to_python(' on').cmd1, '11')
        
        # Trailing space
        self.assertEqual(ic_field.to_python('on ').cmd1, '11')
        
    def test_validate_bad_input(self):
        ic_field = InsteonCommandField('command')
        
        # Bad input
        with self.assertRaises(FieldValidationException) as context:
            ic_field.to_python('self_destruct')
            
    def test_extended_commands(self):
        ic_field = InsteonCommandField('command')
        
        # For a command with an extended data section
        self.assertEqual(ic_field.to_python('thermostat_info').cmd1, '2E')
        self.assertEqual(ic_field.to_python('thermostat_info').cmd2, '02')
        self.assertEqual(ic_field.to_python('thermostat_info').extended, True)
        self.assertEqual(ic_field.to_python('thermostat_info').data, '0000000000000000000000009296')
        
        # For a command without an extended data section
        self.assertEqual(ic_field.to_python('ping').cmd1, '0F')
        self.assertEqual(ic_field.to_python('ping').cmd2, '00')
        self.assertEqual(ic_field.to_python('ping').extended, False)
        self.assertEqual(ic_field.to_python('ping').data, None)
        
        
class InsteonDeviceFieldTest(unittest.TestCase):
    """
    Test the InsteonDeviceField that is used to normalize an Insteon device ID.
    """
    
    def test_validate_good_input(self):
        device_field = InsteonDeviceField('device')
        
        # Good input
        self.assertEqual(device_field.to_python('56:78:9a'), '56789A')
        self.assertEqual(device_field.to_python('56:78:9A'), '56789A')
        self.assertEqual(device_field.to_python('56-78-9f'), '56789F')
        self.assertEqual(device_field.to_python('56.78.9f'), '56789F')
        self.assertEqual(device_field.to_python('56789f'), '56789F')
        self.assertEqual(device_field.to_python('56.789f'), '56789F')
        self.assertEqual(device_field.to_python('56.789f '), '56789F')
        self.assertEqual(device_field.to_python(' 56.789f'), '56789F')
        
    def test_validate_bad_input(self):
        device_field = InsteonDeviceField('device')
        
        # Not long enough
        with self.assertRaises(FieldValidationException) as context:
            device_field.to_python('56:78:9')
            
        # Too long
        with self.assertRaises(FieldValidationException) as context:
            device_field.to_python('56:78:9a1')
            
        # Non-hex characters
        with self.assertRaises(FieldValidationException) as context:
            device_field.to_python('56:78:9g')
            
class InsteonMultipleDeviceFieldTest(unittest.TestCase):
    """
    Test the InsteonMultipleDeviceField that is used to normalize Insteon device IDs.
    """
    
    def test_validate_good_input(self):
        devices_field = InsteonMultipleDeviceField('device')
        
        # Good input
        self.assertEqual(devices_field.to_python('56:78:9a,56:78:9a'), set(['56789A']))
        self.assertEqual(devices_field.to_python('56:78:9A'), set(['56789A']))
        self.assertEqual(len(devices_field.to_python('56-78-9f,56-78-9a')), 2)
        
    def test_validate_bad_input(self):
        devices_field = InsteonMultipleDeviceField('device')
        
        # Not long enough
        with self.assertRaises(FieldValidationException) as context:
            devices_field.to_python('56:78:9')
            
        # Too long
        with self.assertRaises(FieldValidationException) as context:
            devices_field.to_python('56:78:9a,56:78:9a1')
            
        # Non-hex characters
        with self.assertRaises(FieldValidationException) as context:
            devices_field.to_python('56:78:9g')
        
        
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suites = []
    suites.append(loader.loadTestsFromTestCase(ModularAlertTest))
    suites.append(loader.loadTestsFromTestCase(SendInsteonCommandAlertTest))
    suites.append(loader.loadTestsFromTestCase(InsteonCommandFieldTest))
    suites.append(loader.loadTestsFromTestCase(InsteonDeviceFieldTest))
    suites.append(loader.loadTestsFromTestCase(InsteonMultipleDeviceFieldTest))
    suites.append(loader.loadTestsFromTestCase(IPAddressFieldTest))
    suites.append(loader.loadTestsFromTestCase(InsteonExtendedDataFieldTest))
    
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suites))