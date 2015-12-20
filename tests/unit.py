# coding=utf-8
import unittest
import sys
import os
import json
import re
import time
from StringIO import StringIO


sys.path.append( os.path.join("..", "src", "bin") )

from send_insteon_command import InsteonCommandField,  SendInsteonCommandAlert
from insteon_alert_app.modular_alert import ModularAlert, Field, BooleanField, FieldValidationException

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
                
            def run(self, cleaned_params, payload, out_stream):
                
                print >> out_stream, "Alert ran successfully " + self.create_event_string(cleaned_params)
                
                
        return TestModularAlert()
    
    def test_modular_alert_validation(self):
        
        test_instance = self.get_modular_alert_instance()
        
        # Ok input
        self.assertTrue(test_instance.validate({'foo' : 'foo', 'bar' : 'true'})['bar'])
        
        # Bad input
        with self.assertRaises(FieldValidationException) as context:
            test_instance.validate({'foo' : 'foo', 'bar' : '65'})
            
    def test_modular_alert_run(self):
        
        test_instance = self.get_modular_alert_instance()
        
        out_stream = StringIO()
        in_stream = FakeInputStream()
        
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
        
        test_instance.execute(in_stream, out_stream)
        
        self.assertEquals( len(re.findall("Alert ran successfully", out_stream.getvalue())), 1)
        
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
        
    def test_send_command(self):
        
        # Only perform this test if requested
        if self.is_configured():
            
            time.sleep(2)
            insteon_alert = SendInsteonCommandAlert()
            
            out_stream = StringIO()
            
            insteon_alert.call_insteon_web_api_repeatedly(self.address, self.port, self.username, self.password, self.device, "30", "01", out_stream, 3)
            
            self.assertEquals( len(re.findall("Operation performed successfully", out_stream.getvalue())), 3)
            
    def test_execute(self):

        # Only perform this test if requested
        if self.is_configured():
            
            time.sleep(2)

            insteon_alert = SendInsteonCommandAlert()
            
            out_stream = StringIO()
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
            
            insteon_alert.execute(in_stream, out_stream)
            
            self.assertEquals( len(re.findall("Operation performed successfully", out_stream.getvalue())), 1)
        
        
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
        
        
        
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suites = []
    suites.append(loader.loadTestsFromTestCase(ModularAlertTest))
    suites.append(loader.loadTestsFromTestCase(SendInsteonCommandAlertTest))
    suites.append(loader.loadTestsFromTestCase(InsteonCommandFieldTest))
    
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suites))