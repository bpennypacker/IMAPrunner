#!/usr/bin/env python
# See http://pymotw.com/2/imaplib/

import argparse
import imaplib
import ConfigParser
import os
import sys
import re
import email
import tempfile
import errno
from subprocess import call

S_DEFAULTS='defaults'
S_DEBUG='debug'
S_ACCOUNT='account'
S_HOSTNAME='hostname'
S_USERNAME='username'
S_PASSWORD='password'
S_USESSL='use_ssl'
S_PORT='port'
S_DESTINATIONS='destinations'
S_FOLDER_COMMANDS='folder_commands'

def open_connection(config):
    """
    Use the parameters in the "account" block of the configuration file
    to establish an IMAP connection, optionally using SSL.
    Returns: imaplib connection object
    """
    for i in [ S_HOSTNAME, S_USERNAME, S_PASSWORD ]:
        if config.has_option(S_ACCOUNT, i) == False:
            print "%s does not exist in configuration file" % (i)
            sys.exit(1)
        
    hostname = config.get(S_ACCOUNT, S_HOSTNAME)
    username = config.get(S_ACCOUNT, S_USERNAME)
    password = config.get(S_ACCOUNT, S_PASSWORD)

    if config.has_option(S_ACCOUNT, S_USESSL):
        use_ssl = config.getboolean(S_ACCOUNT, S_USESSL)
    else:
        use_ssl = False

    if config.has_option(S_ACCOUNT, S_PORT):
        port = config.getint(S_ACCOUNT, S_PORT)
    elif use_ssl:
        port=993
    else:
        port=143

    if config.getboolean(S_DEFAULTS, S_DEBUG):
        print "connecting to %s as %s on port %d. ssl=%s" % (hostname, username, port, use_ssl)

    try:
        if use_ssl:
            connection = imaplib.IMAP4_SSL(hostname, port)
        else:
            connection = imaplib.IMAP4(hostname, port)
        connection.login(username, password)
    except exception, e:
        print e
        sys.exit(1)

    return connection

list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')

def parse_list_response(line):
    """
    Split a line retrieved by the IMAP "list" command into it's three 
    individual components.
    Returns: [ message_flags, delimeter, mailbox_name ]
    """
    flags, delimiter, mailbox_name = list_response_pattern.match(line).groups()
    mailbox_name = mailbox_name.strip('"')
    return (flags, delimiter, mailbox_name)

def process_message(c, msgid, config):
    """
    Retrieve a specific message in RFC822 format, write it to a temporary
    file, invoke the command specified in the configuration file for the
    associated IMAP folder, then delete the tempoary file and move the
    message to the destination IMAP folder.
    Returns: nothing
    """
    typ, msg_data = c.fetch(msgid, '(RFC822)')
 
    if config.getboolean(S_DEFAULTS, S_DEBUG):
        print "fetch(%s): %s" % (msgid, typ)
    
    if typ != 'OK':
        return

    tmpdir = config.get(S_DEFAULTS, 'tmpdir')

    cmd = config.get(S_FOLDER_COMMANDS, mailbox_name)

    if config.has_option(S_DESTINATIONS, mailbox_name):
        dest = config.get(S_DESTINATIONS, mailbox_name)
    else:
        dest = config.get(S_DEFAULTS, 'destination')

    try:
        tf = tempfile.NamedTemporaryFile(dir=tmpdir, delete=False)
    except OSError, e:
        if e.errno == errno.ENOENT:
            print "Temporary directory %s does not exist" % ( tmpdir )
        else:
            print e
        sys.exit(1)

    for part in msg_data:
        if isinstance(part, tuple):
            msg = email.message_from_string(part[1])
            tf.write(msg.as_string())

    tf.close()

    fullcmd = cmd % ( tf.name )

    if config.getboolean(S_DEFAULTS, S_DEBUG):
        print fullcmd

    call(fullcmd, shell=True)
    os.unlink(tf.name)

    typ, data =  c.copy(msgid, dest)

    if config.getboolean(S_DEFAULTS, S_DEBUG):
        print "c.copy(%s, %s): %s" % (msgid, dest, typ)

    if typ == 'OK':
        typ, data = c.store(msgid, '+FLAGS', r'(\Deleted)')
        if config.getboolean(S_DEFAULTS, S_DEBUG):
            print "store(%s, Deleted): %s" % (msgid, typ)

    return


def process_folder(c, folder, config):
    """
    Get a list of all undeleted messages in the specified IMAP folder
    and call process_message for each individual message.  Once complete,
    expunge the folder to purge it of all the deleted messages.
    Returns: nothing
    """

    typ, data = c.select(folder, readonly=False)

    if config.getboolean(S_DEFAULTS, S_DEBUG):
        print "select \"%s\": %s" % (folder, typ)

    if typ != 'OK':
        return

    num_messages = int(data[0])

    if num_messages == 0:
        return

    typ, [ msg_ids ] = c.search(None, '(ALL UNDELETED)')

    if config.getboolean(S_DEFAULTS, S_DEBUG):
        print "search ALL UNDELETED: %s" % (typ)

    if typ != 'OK':
        return

    for id in msg_ids.split():
        process_message(c, id, config)

    typ, data = c.expunge()

    if config.getboolean(S_DEFAULTS, S_DEBUG):
        print "expunge: %s" % (typ)

    return

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="IMAP Runner")
    parser.add_argument('-c', '--config', help="Configuration file. Default: ~/.imaprunner", required=False, default='~/.imaprunner')
    parser.add_argument('-d', '--debug', help="Debug", required=False, default=False, action='store_true')

    args = parser.parse_args()

    # Read the config file
    config = ConfigParser.ConfigParser()

    if os.path.isfile(args.config):
        try:
            config.read([os.path.expanduser(args.config)])
        except Exception, e:
            print e
            sys.exit(1)
    else:
        print "File %s does not exist" % (args.config)
        sys.exit(1)

    # if -d was specified on the command line then force debug to true
    # in the config object
    if args.debug:
        config.set(S_DEFAULTS, S_DEBUG, 'true')

    c = open_connection(config)

    try:
        typ, data = c.list()
        if config.getboolean(S_DEFAULTS, S_DEBUG):
            print "list: %s" % (typ)
    except e:
        print e
        sys.exit(1)

    for line in data:
        flags, delimiter, mailbox_name = parse_list_response(line)
        if config.getboolean(S_DEFAULTS, S_DEBUG):
            print "mailbox: %s" % (mailbox_name)
        if config.has_option(S_FOLDER_COMMANDS, mailbox_name):
            process_folder(c, mailbox_name, config)
 
    
    c.logout()

