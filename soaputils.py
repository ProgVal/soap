###
# This file is part of Soap.
#
# Soap is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, version 2.
#
# Soap is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should have received
# a copy of the GNU General Public License along with Soap. If not, see
# <http://www.gnu.org/licenses/>.
###

import supybot.conf as conf
import supybot.ircdb as ircdb
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils

import logging
import logging.handlers
import os.path
import re
import urllib2

from enums import *
from libottdadmin2.enums import Colour, Action, DestType, ClientID
from libottdadmin2.packets.admin import AdminRcon, AdminChat
from libottdadmin2.trackingclient import MappingObject

class RconResults(MappingObject):
    _mapping = [
        ('irc', 'irc'),
        ('command', 'command'),
        ('succestext', 'succestext'),
        ('results', 'results'),
    ]

def checkPermission(irc, msg, channel, allowOps):
    capable = ircdb.checkCapability(msg.prefix, 'trusted')
    if capable:
        return True
    else:
        opped = msg.nick in irc.state.channels[channel].ops
        if opped and allowOps:
            return True
        else:
            return False

def disconnect(conn, forced):
    if forced:
        conn.force_disconnect()
    else:
        conn.disconnect()

def generateDownloadUrl(irc, version, osType = None):
    stable = '\d\.\d\.\d'
    testing = '\d\.\d\.\d-rc\d'
    trunk = 'r\d{5}'

    if not osType:
        url = 'http://www.openttd.org/en/'
        if re.match(stable, version) or re.match(testing, version):
            url += 'download-stable/%s' % version
        elif re.match(trunk, version):
            url += 'download-trunk/%s' % version
        else:
            url = None
    else:
        url = 'http://binaries.openttd.org/'
        if re.match(stable, version):
            url += 'releases/%s/openttd-%s-' % (version, version)
        elif re.match(trunk, version):
            url += 'nightlies/trunk/%s/openttd-trunk-%s-' % (version, version)
        else:
            url = None
        if url:
            if osType.startswith('lin'):
                url += 'linux-generic-'
                if osType == 'lin':
                    url += 'i686.tar.xz'
                elif osType == 'lin64':
                    url += 'amd64.tar.xz'
                else:
                    url = None
            elif osType == 'osx':
                url += 'macosx-universal.zip'
            elif osType == 'source':
                url += 'source.tar.xz'
            elif osType.startswith('win'):
                url += 'windows-%s.zip' % osType
            else:
                url = None
    return url

def getColourNameFromNumber(number):
    colours = {
        Colour.COLOUR_DARK_BLUE    : 'Dark Blue',
        Colour.COLOUR_PALE_GREEN   : 'Pale Green',
        Colour.COLOUR_PINK         : 'Pink',
        Colour.COLOUR_YELLOW       : 'Yellow',
        Colour.COLOUR_RED          : 'Red',
        Colour.COLOUR_LIGHT_BLUE   : 'Light Blue',
        Colour.COLOUR_GREEN        : 'Green',
        Colour.COLOUR_DARK_GREEN   : 'Dark Green',
        Colour.COLOUR_BLUE         : 'Blue',
        Colour.COLOUR_CREAM        : 'Cream',
        Colour.COLOUR_MAUVE        : 'Mauve',
        Colour.COLOUR_PURPLE       : 'Purple',
        Colour.COLOUR_ORANGE       : 'Orange',
        Colour.COLOUR_BROWN        : 'Brown',
        Colour.COLOUR_GREY         : 'Grey',
        Colour.COLOUR_WHITE        : 'White',
    }
    colourName = colours.get(number, number)
    return colourName

def getQuitReasonFromNumber(number):
    reasons = {
        0x00 :'general error',
        0x01 :'desync error',
        0x02 :'could not load map',
        0x03 :'connection lost',
        0x04 :'protocol error',
        0x05 :'NewGRF mismatch',
        0x06 :'not authorized',
        0x07 :'received invalid or unexpected packet',
        0x08 :'wrong revision',
        0x09 :'name already in use',
        0x0A :'wrong password',
        0x0B :'wrong company in DoCommand',
        0x0C :'kicked by server',
        0x0D :'was trying to use a cheat',
        0x0E :'server full',
        0x0F :'was sending too many commands',
        0x10 :'received no password in time',
        0x11 :'general timeout',
        0x12 :'downloading map took too long',
        0x13 :'processing map took too long',
    }
    reasonText = reasons.get(number, number)
    return reasonText

def getConnection(connections, channels, source, serverID = None):
    conn = None

    if not serverID:
        if ircutils.isChannel(source) and source.lower() in channels:
            conn = connections.get(source)
    else:
        if ircutils.isChannel(serverID):
            conn = connections.get(serverID)
        else:
            for c in connections.itervalues():
                if c.ID == serverID.lower():
                    conn = c
    return conn

def initLogger(conn, logdir, history):
    if os.path.isdir(logdir):
        if not len(conn.logger.handlers):
            logfile = os.path.join(logdir, '%s.log' % conn.channel)
            logformat = logging.Formatter('%(asctime)s %(message)s')
            handler = logging.handlers.RotatingFileHandler(logfile, backupCount = history)
            handler.setFormatter(logformat)
            conn.logger.addHandler(handler)

def logEvent(logger, message):
    try:
        logger.info(message)
    except AttributeError:
        pass

def msgChannel(irc, channel, msg):
    if channel in irc.state.channels or irc.isNick(channel):
        irc.sendMsg(ircmsgs.privmsg(channel, msg))

def moveToSpectators(irc, conn, client):
    text = '%s: Please change your name before joining/starting a company' % client.name
    command = 'move %s 255' % client.id
    conn.rcon = conn.channel

    conn.send_packet(AdminRcon, command = command)
    conn.send_packet(AdminChat,
        action = Action.CHAT,
        destType = DestType.BROADCAST,
        clientID = ClientID.SERVER,
        message = text)
    msgChannel(irc, conn.channel, text)

def ofsGetsaveExitcodeToText(number):
    texts = {
        0x00 :'',
        0x01 :'Invalid directory in ofs-getsave.py. Please configure it accordingly',
        0x02 :'Couldn\'t save game to disk',
        0x03 :'URL did not lead to a valid savegame. Please check the url in your browser',
    }
    text = texts.get(number, number)
    return text

def ofsStartExitcodeToText(number):
    texts = {
        0x00 :'',
        0x01 :'OpenTTD appears to be running already. Try !apconnect instead',
        0x02 :'OpenTTD was started succesfully, but openttd.pid could not be updated',
        0x03 :'Could not start OpenTTD. Check the configuration of ofs-start.py',
        0x04 :'Started OpenTTD, but couldn\'t read a valid pid from the output. Likely something went wrong',
    }
    text = texts.get(number, number)
    return text

def ofsSvnToBinExitcodeToText(number):
    texts = {
        0x00 :'',
        0x01 :'Copying the new executable to the server directory did not succeed',
    }
    text = texts.get(number, number)
    return text

def ofsSvnUpdateExitcodeToText(number):
    texts = {
        0x00 :'',
        0x01 :'Source directory does not seem to exist. Please check ofs-svnupdate.py configuration',
        0x02 :'Invalid branch selected in ofs-svnupdate.py\'s configuration. Please use nightlies/trunk, stable or testing',
        0x03 :'Something went wrong executing make or svn. Please run ofs-svnupdate.py manually and see what goes wrong',
    }
    text = texts.get(number, number)
    return text

def ofsTransferSaveExitcodeToText(number):
    texts = {
        0x00 :'',
        0x01 :'File already exists, not transferring savegame',
        0x02 :'Missing either game ID or savegame, or possibly both',
        0x03 :'SSH configuration invalid. Please review ofs-transfersave.py\'s configuration',
        0x04 :'Couldn\'t find file, please specify a valid savegame',
        0x05 :'Failed to trasfer the savegame. Please run ofs-transfersave manually to see what causes this',
    }
    text = texts.get(number, number)
    return text

def refreshConnection(connections, registeredConnections, conn):
    try:
        del registeredConnections[conn.filenumber]
    except KeyError:
        pass
    newconn = conn.copy()
    connections[conn.channel] = newconn
    return newconn
