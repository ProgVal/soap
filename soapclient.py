
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

from libottdadmin2.trackingclient import TrackingAdminClient
from libottdadmin2.event import Event

class SoapEvents(object):
    def __init__(self):
        # self.connected      = Event()
        # self.disconnected   = Event()

        # self.shutdown       = Event()
        # self.new_game       = Event()

        # self.new_map        = Event()
        # self.protocol       = Event()

        # self.datechanged    = Event()

        # self.clientinfo     = Event()
        self.clientjoin     = Event()
        self.clientupdate   = Event()
        self.clientquit     = Event()

        # self.companyinfo    = Event()
        # self.companynew     = Event()
        # self.companyupdate  = Event()
        # self.companyremove  = Event()
        # self.companystats   = Event()
        # self.companyeconomy = Event()

        self.chat           = Event()
        # self.rcon           = Event()
        # self.console        = Event()

        # self.pong           = Event()

class SoapClient(TrackingAdminClient):



    # Initialization & miscellanious functions

    def __init__(self, events = None):
        super(SoapClient, self).__init__(events)
        self.soapEvents = SoapEvents()
        self._attachEvents()

    def _attachEvents(self):
        self.events.clientjoin      += self._rcvClientJoin
        self.events.clientupdate    += self._rcvClientUpdate
        self.events.clientquit      += self._rcvClientQuit
        self.events.chat            += self._rcvChat

    def copy(self):
        obj = SoapClient(self.events)
        for prop in self._settable_args:
            setattr(obj, prop, getattr(self, prop, None))
        return obj



    # Insert connection and irc info into parameters

    def _rcvChat(self, **kwargs):
        data = dict(kwargs.items())
        data['connChan'] = self._channel
        self.soapEvents.chat(**data)

    def _rcvClientJoin(self, client):
        self.soapEvents.clientjoin(self._channel, client)

    def _rcvClientQuit(self, client, errorcode):
        self.soapEvents.clientquit(self._channel, client, errorcode)

    def _rcvClientUpdate(self, old, client, changed):
        self.soapEvents.clientupdate(self._channel, old, client, changed)



    # Store some extra info

    _settable_args = TrackingAdminClient._settable_args + [
        'irc', 'ID', 'channel',
        'autoConnect', 'allowOps', 'playAsPlayer', 'polling']
    _irc = None
    _ID = 'Default'
    _channel = None
    _autoConnect = False
    _allowOps = False
    _polling = False
    _playAsPlayer = True
    _registered = False

    @property
    def irc(self):
        return self._irc

    @irc.setter
    def irc(self, value):
        self._irc = value

    @property
    def ID(self):
        return self._ID

    @ID.setter
    def ID(self, value):
        self._ID = value

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        self._channel = value.lower()

    @property
    def autoConnect(self):
        return self._autoConnect

    @autoConnect.setter
    def autoConnect(self, value):
        self._autoConnect = value

    @property
    def allowOps(self):
        return self._allowOps

    @allowOps.setter
    def allowOps(self, value):
        self._allowOps = value

    @property
    def polling(self):
        return self._polling

    @polling.setter
    def polling(self, value):
        self._polling = value

    @property
    def playAsPlayer(self):
        return self._playAsPlayer

    @playAsPlayer.setter
    def playAsPlayer(self, value):
        self._playAsPlayer = value

    @property
    def registered(self):
        return self._registered

    @registered.setter
    def registered(self, value):
        self._playAsPlayer = value