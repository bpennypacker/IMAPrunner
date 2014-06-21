IMAPrunner
==========

IMAPrunner is a relatively simple Python script that allows you to invoke
commands against e-mail messages in specific IMAP mail folders. It came 
about from a desire to learn the basics of Python programming and to also
have a tool with which to easily process spam and other e-mails.

When IMAPrunner is invoked it traverses all the IMAP folders in the
specified account.  If a folder is found that is referenced in the 
configuration file then each message in the folder is written to a temporary
file and then the command specified in the configuration file is invoked
to process the message.  Once the message has been processed the temporary 
file is deleted and the message is moved to a destination folder 
(default: Trash).  

A common use for IMAPrunner would be to set up a cron job that processes
spam messages that you put in a particular folder.  The example configuration
file defines two folders, "spam" and "ham".  Messages that are placed in the 
"spam" folder will be passed to the process_spam.sh script, while messages
that are placed in the "ham" folder are passed to SpamAssassins sa-learn
utility.  "ham" e-mails are then moved to a subfolder called "done" while
"spam" emails are moved to the Trash folder.

Quick Start Guide
=================

Edit imaprunner.cfg.  It is very straightforward and commented.  There
are four sections to the cfg file:

    - The [account] section is where you specify all the login details
      for accessing your IMAP server.  Both plaintext and SSL connections are 
      supported.

    - The [defaults] section contains a few default settings for the 
      script.  The most important setting here is "destination" which 
      specifies the name of the IMAP folder that all messages will be
      moved to by default.  The default destination can be overridden
      on a folder-by-folder basis.

    - The [folder_commands] section contains a list of folder names
      and the commands to invoke against each message in the folder.
      Example:

          spam=/path/to/process_spam.sh %s

      This entry means that all messages found in the "spam" folder will
      be passed to the process_spam.sh script.  The "%s" in the command
      line will be replaced by the name of the temporary file containing
      the full e-mail message (headers & body).

    - The [destinations] section contains overrides for folders to move
      messages to.  If you want messages from a specific folder moved
      to a location different than the default destination then simply
      specify it here.

IMAPrunner by default reads its configuration from ~/.imaprunner or you 
can pass the name of a configuation file using -c:

./imaprunner.py -c imaprunner.cfg

Hint to help getting started: First set up the [account] section of the
configuration file then run IMAPrunner in debug mode.  This can be done
by either setting debug=1 in the configuration file or using -d on the
command line:

./imaprunner.py -c imaprunner.cfg -d

Assuming the login credentials are correct, IMAPrunner will log into your
mail account and display a list of all the mailboxes.  Use the list of
mailboxes as IMAPrunner reports them to then set up the other sections
of the configuration file.

      
