import cloudshell.api.cloudshell_api as cs_api
import time

from cloudshell.api.common_cloudshell_api import CloudShellAPIError
from json import dumps
from lib.yaml_config import YamlConfig
from sys import argv


class ResourceAvailability(object):
    CONFIG_FILE = '/usr/src/script/config/resource_availability_config.yml'
    CONFIG_FILE_TEMPLATE = '/usr/src/script/resource_availability/config/resource_availability_config.template.yml'

    def __init__(self):
        self.reservation_report = []
        self.resource_list = []
        self.start_time = ''
        self.end_time = ''

        self.config = YamlConfig(self.CONFIG_FILE, self.CONFIG_FILE_TEMPLATE)
        self.param = self.config.param

        try:
            self.cs_session = cs_api.CloudShellAPISession(host=self.param['cloudshell_server'],
                                                          username=self.param['cloudshell_user'],
                                                          password=self.param['cloudshell_password'],
                                                          domain=self.param['cloudshell_domain'],
                                                          port=8029)
        except CloudShellAPIError as e:
            msg = "%s\n" \
                  "Critical Error connecting to CloudShell\n" \
                  "%s attempting to start CloudShell API Session\n" \
                  "Server: %s" % (
                      self._get_dts(),
                      argv[0],
                      self.param['cloudshell_server'])

            print '%s\n%s' % (msg, e.message)

    def _get_dts(self):
        """
        Pulls the current local time
        :return: time.strftime: Current Time in ISO8601
        """
        return time.strftime('%Y-%m-%d %H:%M:%S')

    def _resource_exists(self, device_name):
        """
        Boolean query to see if a device exists in inventory
        :param string device_name: the name of the device to query 
        :return: boolean 
        """
        try:
            self.cs_session.GetResourceDetails(resourceFullPath=device_name)
        except CloudShellAPIError:
            return False

        return True

    def _convert_to_ISO8601(self, dts_in=''):
        """
        Converts the std CloudShell API time returned into the ISO8601 Date format.
        Preserves the return's Hour/Min in the 24hr clock
        :param string dts_in: Time string formatted from the CloudShell API return
        :return: string formatted time:  
        """
        date, time = dts_in.split(' ', 1)
        month, day, year = date.split('/')

        return '%s-%s-%s %s' % (year, month, day, time)

    def get_reservations(self, device_name, start_time='', end_time=''):
        """
        This pulls all reservations for a given device in the listed time range, 
        and add them to the Reservation Report
        :param string device_name: Full Name of Resource in Question
        :param string start_time: Start of search period "DD/MM/YYYY HH:MM" in GMT
        :param string end_time: End of search period "DD/MM/YYYY HH:MM" in GMT
        :rtype: FindResourceListInfo
        """
        item_list = self.cs_session.GetResourceAvailabilityInTimeRange(resourcesNames=[device_name],
                                                                       startTime=start_time,
                                                                       endTime=end_time,
                                                                       showAllDomains=True).Resources

        # Thi is how do format for AmCharts - requires reservation_report to be a list
        for item in item_list:
            if item.FullName == device_name:
                temp_d = dict()
                temp_d['category'] = device_name
                temp_d['segments'] = []
                for each in item.Reservations:
                    inner = dict()
                    inner['start'] = self._convert_to_ISO8601(each.StartTime)
                    inner['end'] = self._convert_to_ISO8601(each.EndTime)
                    inner['task'] = '%s owned by: %s (%s)' % (each.ReservationName, each.Owner, each.ReservationId)
                    temp_d['segments'].append(inner)

                temp_d['segments'] = sorted(temp_d['segments'], key=lambda k: k['end'], reverse=True)
                self.reservation_report.append(temp_d)

    def generate_resource_list(self):
        """
        Generates a complete list of resources based on the Family/Model lookup
        The search terms are entries in the 'fam_model_list' in the Configs
        Each entry should be: '<FamilyName>:<ModelName>' - either can be omitted, but not both
        :return: 
        """
        for entry in self.param['family_model_list']:
            family, model = entry.split(':', 1)
            self.resource_list += self.cs_session.FindResources(resourceFamily=family, resourceModel=model).Resources

    def generate_start_end_time(self):
        """
        Generates the query start and end times based on the Offset in the config file.
        The offsets are represented in seconds from the current time.
        Negative numbers are allowed.
        The End Time must be later that the Start time
        """
        start_offset = self.param['start_offset'] + time.timezone  # +Timezone adjusts for GMT
        end_offset = self.param['end_offset'] + time.timezone

        start_intm = time.localtime(time.mktime(time.localtime()) + start_offset)
        end_intm = time.localtime(time.mktime(time.localtime()) + end_offset)

        if start_intm > end_intm:
            raise Exception('End time is before Start Time - Check the config offsets')

        self.start_time = time.strftime('%d/%m/%Y %H:%M', start_intm)
        self.end_time = time.strftime('%d/%m/%Y %H:%M', end_intm)

    def get_availability(self):
        """
        Writes the JSON data file for consumption by AmCharts
        :return: None
        """
        self.generate_start_end_time()
        self.generate_resource_list()

        for resource in self.resource_list:
            if self._resource_exists(resource.Name):
                self.get_reservations(device_name=resource.Name, start_time=self.start_time, end_time=self.end_time)

        amchart_json = dumps(self.reservation_report,
                             sort_keys=False,
                             indent=4,
                             separators=(',', ': '))

        with open(self.param['output_file'], 'w') as f:
            f.write(amchart_json)
            f.close()
