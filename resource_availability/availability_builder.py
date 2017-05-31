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
        self.resource_by_name = []
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

    def get_reservations(self, resource_list, start_time='', end_time=''):
        """
        This pulls all reservations for a given device in the listed time range,
        and add them to the Reservation Report
        :param list resource_list: List of resource names
        :param string start_time: Start of search period "DD/MM/YYYY HH:MM" in GMT
        :param string end_time: End of search period "DD/MM/YYYY HH:MM" in GMT
        :return:
        """
        resource_info_list = self.cs_session.GetResourceAvailabilityInTimeRange(resourcesNames=resource_list,
                                                                                startTime=start_time,
                                                                                endTime=end_time,
                                                                                showAllDomains=True).Resources

        for resource in resource_info_list:
            if resource.FullName in resource_list:
                entry = dict()
                entry['category'] = resource.Name
                entry['segments'] = []
                for reservation in resource.Reservations:
                    segment = dict()
                    segment['end'] = self._convert_to_ISO8601(reservation.EndTime)
                    segment['id'] = reservation.ReservationId
                    segment['name'] = reservation.ReservationName
                    segment['owner'] = reservation.Owner
                    segment['start'] = self._convert_to_ISO8601(reservation.StartTime)

                    entry['segments'].append(segment)

                entry['segments'] = sorted(entry['segments'], key=lambda k: k['end'], reverse=True)
                self.reservation_report.append(entry)

    def generate_resource_list(self):
        """
        Generates a complete list of resources based on the Family/Model lookup
        The search terms are entries in the 'fam_model_list' in the Configs
        Each entry should be: '<FamilyName>:<ModelName>' - either can be omitted, but not both
        :return:
        """

        self.resource_list = []
        for entry in self.param['family_model_list']:
            family, model = entry.split(':', 1)
            resources = self.cs_session.FindResources(resourceFamily=family, resourceModel=model).Resources

            self.resource_list += [resource.Name for resource in resources]

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

        self.get_reservations(resource_list=self.resource_list, start_time=self.start_time, end_time=self.end_time)

        with open(self.param['output_file'], 'w') as f:
            f.write(dumps(self.reservation_report, sort_keys=False, indent=4, separators=(',', ': ')))
