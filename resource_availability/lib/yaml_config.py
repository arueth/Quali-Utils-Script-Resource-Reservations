from os import environ, path
from re import compile
from shutil import copy
from yaml import add_constructor, add_implicit_resolver, load


class YamlConfig:
    ENVIRONMENT_VARIABLE_REGEX = compile(r'^<%=\s*environ\[\'(.*)\'\]\s*%>$')
    FILE_REGEX = compile(r'^<%=\s*file\[\'(.*)\'\]\s*%>$')

    def __init__(self, config_file, template_file):
        self.config_file = config_file
        self.template_file = template_file

        if environ.get('RESOURCE_AVAILABILITY_OVERWRITE_CONFIG') or not path.isfile(self.config_file):
            copy(self.template_file, self.config_file)

        add_implicit_resolver("!env_regex", self.ENVIRONMENT_VARIABLE_REGEX)
        add_implicit_resolver("!file_regex", self.FILE_REGEX)

        add_constructor('!env_regex', self.env_regex_constructor)
        add_constructor('!file_regex', self.file_regex_constructor)

        with open(self.config_file, 'r') as yml_file:
            self.param = load(yml_file)

        return

    def env_regex_constructor(self, loader, node):
        value = loader.construct_scalar(node)
        environment_variable = self.ENVIRONMENT_VARIABLE_REGEX.match(value).group(1)

        if environ.get(environment_variable) is None:
            raise self.EnvironmentVariableDoesNotExists("Environment variable '%s' specified in the configuration file does not exist!" % environment_variable)

        return environ[environment_variable]

    def file_regex_constructor(self, loader, node):
        value = loader.construct_scalar(node)
        file_path = self.FILE_REGEX.match(value).group(1)

        if path.isfile(file_path) is None:
            raise self.FileDoesNotExists("File '%s' specified in the configuration file does not exist!" % file_path)

        f = open(file_path, 'r')
        file_content = f.read()
        f.close()

        file_content = file_content.strip()
        if '\n' in file_content:
            file_content = file_content.split('\n')

        return file_content

    class EnvironmentVariableDoesNotExists(Exception):
        pass

    class FileDoesNotExists(Exception):
        pass
