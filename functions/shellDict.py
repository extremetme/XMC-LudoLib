#
# Shell dictionary
# shellDict.py
#

Shell_Dict = { # Dictionary of all Linux shell commands used by this script
    'list_ntp_servers'           : 'list://ntpq -pn ||^[*+](\d+\.\d+\.\d+\.\d+)',
#    'get_time_zone'              : 'tuple://date +%Z%z ||^(\w+)([-+]\d\d)(\d\d)',
    'get_time_zone'              : 'tuple:// timedatectl ||Time zone: (\S+?)(?:/(\S+?))? \((\w+?), ([-+]\d\d)(\d\d)\)',
    'check_file_exists'          : 'bool://ls {1}{0}||^{1}{0}$', # Filename, Path
    'get_file_size'              : 'str://ls -l {1}{0}||(\d\d\d\d\d+) +\S+ +\S+ +\S+ +{1}{0} *$', # Filename, Path
    'grep_syslog_to_file'        : 'grep "{}" {} > {}', # Match string, File list (space separated), Output file
}
