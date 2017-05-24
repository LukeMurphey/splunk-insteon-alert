================================================
Overview
================================================

This app provides a mechanism for controlling Insteon devices from Splunk.



================================================
Configuring Splunk
================================================

Install this app into Splunk by doing the following:

  1. Log in to Splunk Web and navigate to "Apps » Manage Apps" via the app dropdown at the top left of Splunk's user interface
  2. Click the "install app from file" button
  3. Upload the file by clicking "Choose file" and selecting the app
  4. Click upload
  5. Restart Splunk if a dialog asks you to

Configure the Insteon Alert app once you have it installed:

  1. Select "Settings » Alert actions" from the menu at the top right of Splunk
  2. Click the link namted "Setup Insteon Alert" in the row of the "Execute Insteon command" action

This app also includes a search command for executing Insteon commands. You can run this search using " | insteoncommand".



================================================
Getting Support
================================================

Go to the following website if you need support:

     http://answers.splunk.com/answers/app/2994

You can access the source-code and get technical details about the app at:

     https://github.com/LukeMurphey/splunk-insteon-alert



================================================
Change History
================================================

+---------+------------------------------------------------------------------------------------------------------------------+
| Version |  Changes                                                                                                         |
+---------+------------------------------------------------------------------------------------------------------------------+
| 0.5     | Initial release                                                                                                  |
|---------|------------------------------------------------------------------------------------------------------------------|
| 0.6     | Fixing the license link on the setup page and updating the icons                                                 |
|         | Logs now show up when following the link to see events from the manager                                          |
|---------|------------------------------------------------------------------------------------------------------------------|
| 0.7     | Set the source-typing of internal search command logs                                                            |
|         | Added the ability to send extended-direct commands                                                               |
|         | Fixed issue where the commands with a single digit did not have leading zeroes added properly                    |
+---------+------------------------------------------------------------------------------------------------------------------+
